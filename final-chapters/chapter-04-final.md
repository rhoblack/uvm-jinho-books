# Chapter 4: UVM 기본 컴포넌트

> **학습 목표**
> - `uvm_object`와 `uvm_component`의 차이를 이해한다
> - UVM Factory 패턴의 동작 원리를 이해하고, `type_id::create()`를 사용할 수 있다
> - Phase 메커니즘의 실행 순서를 이해하고, 각 Phase의 역할을 안다
> - `` `uvm_component_utils ``와 `` `uvm_object_utils `` 매크로의 역할을 안다
> - 간단한 UVM 컴포넌트를 직접 작성하고 실행할 수 있다

> **선수 지식**: Chapter 3에서 배운 클래스(class), 상속(extends), 다형성(virtual), 생성자(new)를 사용합니다. 특히 "부모 클래스를 extends로 확장한다"는 개념이 핵심입니다.

---

## 4.1 UVM 클래스 계층 구조

> **이 절의 목표**: UVM의 모든 클래스가 하나의 계층 트리에서 시작한다는 것을 이해하고, `uvm_object`와 `uvm_component`의 차이를 명확히 구분합니다.

### 4.1.1 UVM은 거대한 클래스 라이브러리

Chapter 3에서 class와 extends를 배웠습니다. UVM은 이 기능을 사용하여 만들어진 **거대한 클래스 라이브러리**입니다. UVM을 처음 배울 때 압도당하는 이유는 클래스가 수백 개이기 때문인데, 실제로 우리가 직접 다루는 클래스는 10개 미만입니다.

핵심만 보면 UVM의 클래스 계층은 매우 단순합니다:

```
uvm_void                          ← 최상위 (거의 사용 안 함)
  └─ uvm_object                   ← 모든 UVM 클래스의 기반
       ├─ uvm_transaction         ← 데이터를 담는 클래스들
       │    └─ uvm_sequence_item  ← 트랜잭션 (Chapter 6)
       │
       ├─ uvm_sequence            ← 시퀀스 (Chapter 6)
       │
       └─ uvm_component           ← 테스트벤치 구조를 만드는 클래스들
            ├─ uvm_test            ← 테스트 (Chapter 1-2에서 사용!)
            ├─ uvm_env             ← 환경
            ├─ uvm_agent           ← 에이전트
            ├─ uvm_driver          ← 드라이버 (Chapter 7)
            ├─ uvm_monitor         ← 모니터 (Chapter 7)
            ├─ uvm_sequencer       ← 시퀀서 (Chapter 6)
            └─ uvm_scoreboard      ← 스코어보드 (Chapter 8)
```

> **참고**: 위 계층도는 학습에 필요한 핵심 클래스만 표시한 것입니다. 실제 UVM 라이브러리에는 중간 단계의 클래스(uvm_sequence_base, uvm_driver #(REQ,RSP) 등)가 더 있지만, 사용법은 동일하므로 지금은 이 구조만 기억하면 충분합니다.

> **핵심**: 모든 UVM 클래스는 `uvm_object`에서 시작합니다. 그리고 크게 두 가지로 나뉩니다:
> - **uvm_object 계열**: 데이터를 담는 용도 (트랜잭션, 시퀀스)
> - **uvm_component 계열**: 테스트벤치 구조를 만드는 용도 (테스트, 드라이버 등)

### 4.1.2 uvm_object와 uvm_component의 차이

이 둘의 차이가 UVM을 이해하는 첫 번째 관문입니다:

| 비교 항목 | `uvm_object` | `uvm_component` |
|-----------|-------------|-----------------|
| **역할** | 데이터를 담는 그릇 | 테스트벤치의 뼈대(구조) |
| **비유** | 택배 상자 (만들고 버림) | 건물의 방 (한 번 짓고 계속 사용) |
| **생명 주기** | 필요할 때 생성, 사용 후 소멸 | 시뮬레이션 시작 시 생성, 끝까지 유지 |
| **부모-자식 관계** | 없음 | 있음 (트리 구조) |
| **Phase** | 없음 | 있음 (build → connect → run) |
| **생성자** | `new(string name)` | `new(string name, uvm_component parent)` |
| **대표 예시** | 트랜잭션, 시퀀스 | 드라이버, 모니터, 환경 |

```
uvm_object (택배 상자)              uvm_component (건물의 방)
┌──────────────────┐              ┌──────────────────┐
│  시뮬레이션 중     │              │  시뮬레이션 시작 시 │
│  수백~수천 개 생성 │              │  한 번만 생성      │
│  사용 후 버려짐   │              │  끝까지 유지       │
│                  │              │  부모-자식 트리     │
│  예: 패킷 데이터  │              │  예: 드라이버      │
└──────────────────┘              └──────────────────┘
```

> **기억하세요**: "**데이터는 object, 구조는 component**". 택배 상자(object)는 매번 새로 만들지만, 택배 시스템의 분류기(component)는 한 번 설치하고 계속 사용합니다.

### 4.1.3 생성자의 차이 — parent가 핵심

Chapter 3에서 배운 `new()`를 UVM에서는 약간 다르게 사용합니다:

```systemverilog
// uvm_object 계열: 이름만 필요
class my_transaction extends uvm_sequence_item;
  function new(string name = "my_transaction");
    super.new(name);        // 이름만 전달
  endfunction
endclass

// uvm_component 계열: 이름 + 부모(parent) 필요
class my_driver extends uvm_driver;
  function new(string name, uvm_component parent);
    super.new(name, parent);  // 이름과 부모 전달
  endfunction
endclass
```

`uvm_component`에 `parent`가 필요한 이유는 **컴포넌트 트리**를 만들기 위해서입니다:

```
uvm_test_top (테스트)                  ← 트리의 최상위
  └─ env (환경)                        ← parent = uvm_test_top
       └─ agent (에이전트)             ← parent = env
            ├─ driver (드라이버)       ← parent = agent
            ├─ monitor (모니터)        ← parent = agent
            └─ sequencer (시퀀서)      ← parent = agent
```

> **UVM과의 연결**: Chapter 1-2에서 `class hello_test extends uvm_test`를 작성했을 때, UVM이 내부적으로 `hello_test`를 트리의 최상위에 배치했습니다. Chapter 5에서 실제 환경(env), 에이전트(agent)를 추가하면 이 트리가 확장됩니다.

### 4.1.4 실습: uvm_component 기본 예제

Chapter 1-2에서 이미 `uvm_test`를 사용해봤습니다. 이번에는 `uvm_component`를 직접 만들어봅시다:

**[예제 4-1] 간단한 uvm_component 작성**

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 4-1] uvm_component 기본 사용
// 목적: uvm_component 생성, 부모-자식 관계, 기본 Phase 이해
// 시뮬레이터 설정: SystemVerilog, UVM 1.2 (Chapter 2와 동일)

`include "uvm_macros.svh"
import uvm_pkg::*;

// ── 커스텀 컴포넌트 정의 ──
// uvm_component를 extends하여 나만의 컴포넌트를 만듭니다
class my_component extends uvm_component;

  // ⭐ Factory 등록 매크로 (4.2절에서 자세히 설명)
  // 지금은 "이 줄이 있어야 UVM이 이 클래스를 인식한다" 정도로 이해하세요
  `uvm_component_utils(my_component)

  // 생성자: 이름과 부모를 받습니다
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  // build_phase: 시뮬레이션 시작 전, 하위 컴포넌트를 생성하는 단계
  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);  // ⚠️ 반드시 호출! (아래 설명 참조)
    `uvm_info(get_type_name(), "build_phase 실행됨", UVM_MEDIUM)
  endfunction

  // connect_phase: 컴포넌트 간 연결을 설정하는 단계
  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    `uvm_info(get_type_name(), "connect_phase 실행됨", UVM_MEDIUM)
  endfunction

  // run_phase: 실제 시뮬레이션이 실행되는 단계
  virtual task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    `uvm_info(get_type_name(), "run_phase 시작!", UVM_MEDIUM)
    #100;
    `uvm_info(get_type_name(), "run_phase 완료!", UVM_MEDIUM)
    phase.drop_objection(this);
  endtask

endclass

// ── 테스트 클래스 ──
class my_test extends uvm_test;
  `uvm_component_utils(my_test)

  my_component comp;  // 하위 컴포넌트 핸들 선언

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  // build_phase에서 하위 컴포넌트 생성
  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    // ⭐ Factory를 통한 생성 (4.2절에서 자세히 설명)
    comp = my_component::type_id::create("comp", this);
    `uvm_info(get_type_name(), "my_component를 생성했습니다!", UVM_MEDIUM)
  endfunction

endclass

// ── 실행 ──
module top;
  initial begin
    run_test("my_test");
  end
endmodule
```

**예상 출력**:
```
UVM_INFO @ 0: uvm_test_top [my_test] my_component를 생성했습니다!
UVM_INFO @ 0: uvm_test_top.comp [my_component] build_phase 실행됨
UVM_INFO @ 0: uvm_test_top.comp [my_component] connect_phase 실행됨
UVM_INFO @ 0: uvm_test_top.comp [my_component] run_phase 시작!
UVM_INFO @ 100: uvm_test_top.comp [my_component] run_phase 완료!
```

> **관찰 포인트**: 출력에서 `uvm_test_top.comp`라는 경로에 주목하세요. `uvm_test_top`은 UVM이 자동으로 만드는 최상위 이름이고, `comp`는 우리가 `create("comp", this)`에서 지정한 이름입니다. 이것이 컴포넌트 트리의 경로입니다.

> **참고**: 예상 출력의 세부 형식(타임스탬프, 줄 번호 등)은 시뮬레이터에 따라 다를 수 있습니다. `[my_component] build_phase 실행됨` 같은 핵심 메시지가 순서대로 나오면 정상입니다.

> **중요: super.build_phase(phase)를 반드시 호출하세요**
> 위 코드에서 `super.build_phase(phase);`를 빠뜨리면 어떻게 될까요? 겉보기에는 동작하는 것 같지만, Chapter 5에서 배울 `uvm_config_db`(설정값 전달 기능)가 제대로 동작하지 않게 됩니다. UVM의 build_phase는 부모 클래스에서 중요한 초기화 작업을 하므로, **모든 Phase 함수의 첫 줄에 `super.xxx_phase(phase);`를 호출하는 습관**을 들이세요.

---

## 4.2 Factory 패턴 — new() 대신 create()를 쓰는 이유

> **이 절의 목표**: UVM Factory의 필요성을 이해하고, `type_id::create()`로 객체를 생성하는 방법을 익힙니다.

### 4.2.1 먼저 new()로 만들어보면?

Chapter 3에서 객체를 만들 때 `new()`를 사용했습니다. UVM에서도 `new()`로 만들 수 있긴 합니다:

```systemverilog
// ❌ 직접 new()로 생성 (동작하지만 권장하지 않음)
function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  comp = new("comp", this);  // 직접 생성
endfunction
```

이 코드는 동작합니다. 그런데 왜 UVM에서는 `new()` 대신 더 복잡해 보이는 `type_id::create()`를 쓸까요?

### 4.2.2 new()의 문제 — 교체가 안 된다

실무 시나리오로 이해해봅시다:

> **시나리오**: 당신은 UART 검증 환경을 만들었습니다. 기본 드라이버(`uart_driver`)가 잘 동작합니다. 그런데 어느 날 팀장이 말합니다: "에러 주입 기능이 있는 드라이버(`error_uart_driver`)로 바꿔서 테스트해봐."

**new()를 사용했다면:**

```systemverilog
class uart_agent extends uvm_agent;
  uart_driver drv;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    drv = new("drv", this);  // uart_driver로 고정!
  endfunction
endclass
```

`error_uart_driver`로 교체하려면 이 코드를 **직접 수정**해야 합니다:

```systemverilog
// ❌ 코드 직접 수정 필요
drv = new("drv", this);  // 이 줄을 찾아서
// 아래로 변경
error_drv = new("drv", this);  // 이렇게 바꿔야 함
```

프로젝트가 커지면 수십 개의 파일을 수정해야 할 수도 있습니다!

### 4.2.3 Factory의 해결책 — 코드 수정 없이 교체

Factory를 사용하면 **코드를 한 줄도 수정하지 않고** 컴포넌트를 교체할 수 있습니다:

```systemverilog
class uart_agent extends uvm_agent;
  uart_driver drv;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    drv = uart_driver::type_id::create("drv", this);  // Factory를 통한 생성
  endfunction
endclass
```

교체할 때는 **테스트 클래스에서 한 줄만 추가**하면 됩니다. 환경 코드(`uart_agent`)는 전혀 수정할 필요가 없습니다. 이것이 Factory의 핵심 가치입니다.

> **미리보기**: Factory override(교체)의 구체적인 코드와 사용법은 이후 챕터에서 실습합니다. 지금은 "create()를 쓰면 나중에 코드 수정 없이 교체할 수 있다"는 것만 기억하세요.

> **비유**: Factory = **자동차 조립 공장의 부품 교체 시스템**
> - `new()` = 부품을 직접 용접 (교체하려면 용접을 뜯어야 함)
> - `create()` = 부품을 규격화된 슬롯에 끼움 (같은 규격이면 다른 부품으로 바로 교체 가능)

```
new() 방식:                            Factory (create) 방식:
┌─────────────┐                        ┌─────────────┐
│  uart_agent │                        │  uart_agent │
│             │  코드 수정 필요!        │             │  코드 수정 없음!
│  drv = new()│ ──────────────→        │  drv=create()│──→ Factory ──→ 실제 객체
│  (고정됨)   │  error_drv=new()       │  (Factory에 │    ↑
└─────────────┘                        │   요청만 함) │    │ override 설정
                                       └─────────────┘    │
                                                    set_type_override()
```

> **실무 팁**: 팹리스에서 검증 환경을 만들면, 프로젝트 끝날 때까지 수십 번의 변경이 생깁니다. Factory를 사용하면 환경 코드를 수정하지 않고 테스트 클래스에서만 교체할 수 있어서, 코드 안정성이 크게 높아집니다.

> **면접 빈출**: "UVM Factory 패턴을 설명하세요"는 검증 엔지니어 면접에서 가장 자주 나오는 질문 중 하나입니다. "코드 수정 없이 컴포넌트를 교체할 수 있게 해주는 메커니즘"이라고 답하면 됩니다.

### 4.2.4 Factory 사용법 3단계

Factory를 사용하려면 3가지가 필요합니다:

**1단계: Factory에 등록 (매크로)**

```systemverilog
class my_driver extends uvm_driver;
  `uvm_component_utils(my_driver)    // uvm_component 계열
  // ...
endclass

class my_transaction extends uvm_sequence_item;
  `uvm_object_utils(my_transaction)  // uvm_object 계열
  // ...
endclass
```

| 매크로 | 대상 | 용도 |
|--------|------|------|
| `` `uvm_component_utils `` | `uvm_component`를 extends한 클래스 | 컴포넌트를 Factory에 등록 |
| `` `uvm_object_utils `` | `uvm_object`를 extends한 클래스 | 데이터 객체를 Factory에 등록 |

> **기억하세요**: "component에는 `uvm_component_utils`, object에는 `uvm_object_utils`." 매크로 이름이 직관적이라 외우기 쉽습니다.

**2단계: 표준 생성자 작성**

```systemverilog
// uvm_component 계열: 반드시 이 형태
function new(string name, uvm_component parent);
  super.new(name, parent);
endfunction

// uvm_object 계열: 반드시 이 형태
function new(string name = "my_transaction");
  super.new(name);
endfunction
```

> **주의**: 생성자의 형태(파라미터)를 지키지 않으면 Factory가 객체를 만들 수 없어서 에러가 발생합니다. 이것은 UVM의 규칙입니다.

**3단계: create()로 생성**

```systemverilog
// uvm_component 생성 (부모 지정)
my_driver drv;
drv = my_driver::type_id::create("drv", this);

// uvm_object 생성 (부모 없음)
my_transaction txn;
txn = my_transaction::type_id::create("txn");
```

> **패턴 정리**: `클래스명::type_id::create("인스턴스이름", 부모)` — 이 패턴은 UVM 코드에서 수백 번 나옵니다. "클래스이름 콜론콜론 type_id 콜론콜론 create"로 외워두세요.

### 4.2.5 Factory 매크로가 하는 일

`` `uvm_component_utils(my_driver) ``가 뒤에서 하는 일을 간단히 설명하면:

1. **Factory에 등록**: "my_driver라는 클래스가 있다"고 알려줌
2. **type_id 생성**: `my_driver::type_id::create()`를 사용할 수 있게 함
3. **get_type_name() 제공**: 로그에 클래스 이름이 표시됨

> **실무 참고**: 매크로의 내부 동작은 복잡하지만, 사용법은 간단합니다. "class 바로 다음 줄에 매크로를 넣고, 표준 생성자를 작성하고, create()로 생성한다" — 이 3단계만 기억하면 됩니다.

### 4.2.6 흔한 실수: 매크로를 빠뜨리면?

```systemverilog
class my_driver extends uvm_driver;
  // `uvm_component_utils(my_driver)  ← 이 줄을 빠뜨리면!

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
endclass
```

```
에러 메시지:
** Fatal: (SIGSEGV) Bad handle or reference.
또는
UVM_FATAL @ 0: reporter [NOFACTORY] ...
```

**해결**: class 선언 바로 다음 줄에 매크로를 추가하세요. UVM 코드를 작성할 때 습관적으로 "class 선언 → 매크로 → 생성자" 순서를 따르면 실수를 방지할 수 있습니다.

### 4.2.7 Factory 실습 예제

**[예제 4-2] Factory 등록과 create() 사용**

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 4-2] Factory 패턴 기본 실습
// 목적: `uvm_component_utils, `uvm_object_utils, type_id::create() 사용법 이해

`include "uvm_macros.svh"
import uvm_pkg::*;

// ── uvm_object 계열: 트랜잭션 ──
class simple_txn extends uvm_sequence_item;
  `uvm_object_utils(simple_txn)     // ⭐ object 계열 매크로

  rand bit [7:0] addr;
  rand bit [31:0] data;

  function new(string name = "simple_txn");
    super.new(name);               // object: 이름만 전달
  endfunction

  // convert2string(): 트랜잭션의 내용을 한 줄의 문자열로 변환하는 함수
  // 디버깅할 때 `uvm_info로 "이 트랜잭션에 무슨 값이 들어있는지" 확인하려면 필수!
  // UVM의 관례적인 함수명이므로 이 이름을 사용합니다
  virtual function string convert2string();
    return $sformatf("addr=0x%02h, data=0x%08h", addr, data);
  endfunction
endclass

// ── uvm_component 계열: 간단한 프로듀서 ──
class simple_producer extends uvm_component;
  `uvm_component_utils(simple_producer)  // ⭐ component 계열 매크로

  function new(string name, uvm_component parent);
    super.new(name, parent);       // component: 이름 + 부모 전달
  endfunction

  virtual task run_phase(uvm_phase phase);
    simple_txn txn;
    phase.raise_objection(this);

    // Factory로 트랜잭션(uvm_object) 생성
    txn = simple_txn::type_id::create("txn");

    // 랜덤화 (Chapter 3에서 배운 내용!)
    if (!txn.randomize())
      `uvm_fatal(get_type_name(), "랜덤화 실패!")

    `uvm_info(get_type_name(),
      $sformatf("트랜잭션 생성: %s", txn.convert2string()), UVM_MEDIUM)

    #50;
    phase.drop_objection(this);
  endtask
endclass

// ── 테스트 ──
class factory_test extends uvm_test;
  `uvm_component_utils(factory_test)

  simple_producer producer;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    producer = simple_producer::type_id::create("producer", this);
  endfunction
endclass

// ── 실행 ──
module top;
  initial begin
    run_test("factory_test");
  end
endmodule
```

**예상 출력**:
```
UVM_INFO @ 0: uvm_test_top.producer [simple_producer] 트랜잭션 생성: addr=0x1a, data=0x3f2c80a4
```

> **확인해보세요**: (1) `uvm_test_top.producer`라는 컴포넌트 경로가 보이나요? (2) 실행할 때마다 addr과 data 값이 바뀌나요? — 바뀐다면 랜덤화가 정상 동작하는 것입니다.

---

## 4.3 Phase 메커니즘 — 시뮬레이션의 순서 관리

> **이 절의 목표**: UVM Phase의 실행 순서를 이해하고, 각 Phase에서 해야 하는 일과 하지 말아야 하는 일을 구분합니다.

### 4.3.1 Phase가 필요한 이유

일반적인 Verilog 테스트벤치에서는 `initial begin ... end` 안에 모든 것을 넣었습니다. 간단한 DUT에서는 문제없지만, 복잡한 검증 환경에서는 순서가 중요합니다:

```
문제 상황:
1. 드라이버가 데이터를 보내려면 → 먼저 시퀀서와 연결되어야 함
2. 시퀀서와 연결하려면 → 먼저 시퀀서가 생성되어야 함
3. 시퀀서가 생성되려면 → 먼저 에이전트가 생성되어야 함

→ 생성 → 연결 → 실행 순서를 강제할 방법이 필요!
```

UVM Phase는 이 순서를 **자동으로 관리**합니다. "모든 컴포넌트의 build_phase가 끝나야 connect_phase가 시작된다"는 것을 UVM이 보장합니다.

### 4.3.2 핵심 Phase 3가지

UVM에는 여러 Phase가 있지만, 처음에 알아야 할 것은 **3가지**입니다:

```
┌─────────────────────────────────────────────┐
│              build_phase                     │
│  "건설 단계" — 컴포넌트를 만듭니다            │
│  • 하위 컴포넌트 생성 (create)                │
│  • 설정값 적용 (config_db → Ch.5)            │
│  📌 위에서 아래로: test → env → agent → drv   │
│  📌 function (시간 소모 없음)                 │
├─────────────────────────────────────────────┤
│              connect_phase                   │
│  "배선 단계" — 컴포넌트를 연결합니다           │
│  • TLM 포트 연결 (Chapter 7)                 │
│  • 아래에서 위로: drv → agent → env → test   │
│  📌 function (시간 소모 없음)                 │
├─────────────────────────────────────────────┤
│              run_phase                       │
│  "가동 단계" — 실제 시뮬레이션 실행            │
│  • 시퀀스 실행, 데이터 주고받기               │
│  • 모든 컴포넌트가 동시에 실행                │
│  📌 task (시간 소모 있음 — #100, @clk 등)    │
└─────────────────────────────────────────────┘
```

> **비유**: 공장을 떠올려보세요:
> 1. **build_phase** = 기계 설치 (컨베이어, 로봇팔 배치)
> 2. **connect_phase** = 배선 연결 (전선, 파이프 연결)
> 3. **run_phase** = 공장 가동! (제품 생산 시작)
>
> 기계를 설치하기 전에 공장을 가동할 수 없고, 배선 없이 기계가 동작할 수 없습니다. UVM Phase가 이 순서를 보장합니다.

### 4.3.3 Phase의 실행 순서 상세

UVM의 전체 Phase 순서는 다음과 같습니다. **굵은 글씨** 3가지만 먼저 기억하세요:

| 순서 | Phase | 종류 | 역할 | 중요도 |
|------|-------|------|------|--------|
| 1 | **build_phase** | function | 컴포넌트 생성 | 필수 |
| 2 | **connect_phase** | function | 포트 연결 | 필수 |
| 3 | end_of_elaboration_phase | function | 구조 완성 확인 | 선택 |
| 4 | start_of_simulation_phase | function | 시뮬레이션 시작 알림 | 선택 |
| 5 | **run_phase** | task | 시뮬레이션 실행 | 필수 |
| 6 | extract_phase | function | 결과 추출 | 선택 |
| 7 | check_phase | function | 결과 확인 | 선택 |
| 8 | report_phase | function | 보고서 출력 | 선택 |

> **핵심**: build → connect → run, 이 3개만 기억하세요. 나머지 Phase는 필요할 때 배웁니다.

### 4.3.4 build_phase의 실행 순서 — 위에서 아래로

build_phase는 다른 Phase와 달리 **위에서 아래로(Top-Down)** 실행됩니다. 이유는 간단합니다: 부모가 먼저 생성되어야 자식을 만들 수 있으니까요.

```
build_phase 실행 순서 (Top-Down):

  uvm_test_top (my_test)     ← 1번째 실행
       │
       └─ env                ← 2번째 실행
            │
            └─ agent         ← 3번째 실행
                 │
                 ├─ driver   ← 4번째 실행
                 ├─ monitor  ← 5번째 실행
                 └─ sequencer← 6번째 실행
```

다른 Phase(connect, run 등)는 **아래에서 위로(Bottom-Up)** 실행됩니다:

```
connect_phase 실행 순서 (Bottom-Up):

  uvm_test_top (my_test)     ← 6번째 실행
       │
       └─ env                ← 5번째 실행
            │
            └─ agent         ← 4번째 실행
                 │
                 ├─ driver   ← 1번째 실행
                 ├─ monitor  ← 2번째 실행
                 └─ sequencer← 3번째 실행
```

> **기억하세요**: "build는 위에서 아래(부모 먼저), 나머지는 아래에서 위(자식 먼저)." 면접에서도 자주 나오는 질문입니다.

### 4.3.5 Phase에서 하면 안 되는 것

| Phase | 해야 할 일 | 하면 안 되는 일 |
|-------|-----------|---------------|
| build_phase | `create()`로 컴포넌트 생성 | 포트 연결 (아직 생성 안 된 컴포넌트와 연결 시도) |
| connect_phase | 포트/export 연결 | 새 컴포넌트 생성 (build에서 해야 함) |
| run_phase | 시퀀스 실행, 데이터 전송 | 컴포넌트 생성 또는 연결 (이미 끝난 단계) |

```systemverilog
// ❌ 잘못된 예: connect_phase에서 컴포넌트 생성
virtual function void connect_phase(uvm_phase phase);
  super.connect_phase(phase);
  drv = my_driver::type_id::create("drv", this);  // 여기서 하면 안 됨!
endfunction

// ✅ 올바른 예: build_phase에서 생성, connect_phase에서 연결
virtual function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  drv = my_driver::type_id::create("drv", this);  // 생성은 여기서!
endfunction

virtual function void connect_phase(uvm_phase phase);
  super.connect_phase(phase);
  // 연결은 여기서! (Chapter 7에서 자세히 배움)
endfunction
```

### 4.3.6 run_phase와 objection — 시뮬레이션 종료 조건

Chapter 1-2에서 `raise_objection`과 `drop_objection`을 사용했습니다. 이제 왜 필요한지 정확히 이해합시다:

```systemverilog
virtual task run_phase(uvm_phase phase);
  phase.raise_objection(this);   // "아직 할 일이 있어요!" (시뮬레이션 유지)

  // ... 실제 작업 ...

  phase.drop_objection(this);    // "다 끝났어요!" (종료해도 됨)
endtask
```

> **비유**: objection = **비행기 출발 전 승객 탑승**
> - `raise_objection` = "아직 탑승 중입니다!" (문 닫지 마세요)
> - `drop_objection` = "모두 탑승 완료!" (출발해도 됩니다)
> - 아무도 raise하지 않으면 UVM은 "할 일이 없다"고 판단하고 즉시 종료합니다.

**흔한 실수: raise_objection을 빠뜨리면?**

```systemverilog
virtual task run_phase(uvm_phase phase);
  // phase.raise_objection(this);  ← 빠뜨림!
  #100;
  `uvm_info(get_type_name(), "이 메시지는 절대 출력 안 됨!", UVM_MEDIUM)
  // phase.drop_objection(this);
endtask
```

```
결과: run_phase가 시작되자마자 시뮬레이션이 종료됨
→ #100 이전에 이미 끝나버림
```

> **주의**: objection은 run_phase에서만 필요합니다. build_phase와 connect_phase는 function이므로 시간 개념이 없고, UVM이 자동으로 관리합니다.

### 4.3.7 Phase 실습: 실행 순서 확인

**[예제 4-3] Phase 실행 순서 관찰하기**

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 4-3] Phase 실행 순서 관찰
// 목적: build → connect → run 순서와 Top-Down/Bottom-Up 확인

`include "uvm_macros.svh"
import uvm_pkg::*;

// ── 자식 컴포넌트 ──
class child_comp extends uvm_component;
  `uvm_component_utils(child_comp)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    `uvm_info(get_name(), "build_phase 실행", UVM_MEDIUM)
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    `uvm_info(get_name(), "connect_phase 실행", UVM_MEDIUM)
  endfunction

  virtual task run_phase(uvm_phase phase);
    `uvm_info(get_name(), "run_phase 시작", UVM_MEDIUM)
  endtask
endclass

// ── 부모 컴포넌트 ──
class parent_comp extends uvm_component;
  `uvm_component_utils(parent_comp)

  child_comp child_a;
  child_comp child_b;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    `uvm_info(get_name(), "build_phase 실행", UVM_MEDIUM)
    child_a = child_comp::type_id::create("child_a", this);
    child_b = child_comp::type_id::create("child_b", this);
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    `uvm_info(get_name(), "connect_phase 실행", UVM_MEDIUM)
  endfunction

  virtual task run_phase(uvm_phase phase);
    `uvm_info(get_name(), "run_phase 시작", UVM_MEDIUM)
  endtask
endclass

// ── 테스트 ──
class phase_test extends uvm_test;
  `uvm_component_utils(phase_test)

  parent_comp parent;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    `uvm_info(get_name(), "build_phase 실행", UVM_MEDIUM)
    parent = parent_comp::type_id::create("parent", this);
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    `uvm_info(get_name(), "connect_phase 실행", UVM_MEDIUM)
  endfunction

  virtual task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    `uvm_info(get_name(), "run_phase 시작", UVM_MEDIUM)
    #10;
    `uvm_info(get_name(), "run_phase 완료", UVM_MEDIUM)
    phase.drop_objection(this);
  endtask
endclass

module top;
  initial begin
    run_test("phase_test");
  end
endmodule
```

**예상 출력**:
```
UVM_INFO @ 0: uvm_test_top [uvm_test_top] build_phase 실행
UVM_INFO @ 0: uvm_test_top.parent [parent] build_phase 실행
UVM_INFO @ 0: uvm_test_top.parent.child_a [child_a] build_phase 실행
UVM_INFO @ 0: uvm_test_top.parent.child_b [child_b] build_phase 실행
UVM_INFO @ 0: uvm_test_top.parent.child_a [child_a] connect_phase 실행
UVM_INFO @ 0: uvm_test_top.parent.child_b [child_b] connect_phase 실행
UVM_INFO @ 0: uvm_test_top.parent [parent] connect_phase 실행
UVM_INFO @ 0: uvm_test_top [uvm_test_top] connect_phase 실행
UVM_INFO @ 0: uvm_test_top [uvm_test_top] run_phase 시작
UVM_INFO @ 0: uvm_test_top.parent [parent] run_phase 시작
UVM_INFO @ 0: uvm_test_top.parent.child_a [child_a] run_phase 시작
UVM_INFO @ 0: uvm_test_top.parent.child_b [child_b] run_phase 시작
UVM_INFO @ 10: uvm_test_top [uvm_test_top] run_phase 완료
```

> **관찰 포인트**:
> 1. **build_phase**: test → parent → child_a → child_b (위에서 아래)
> 2. **connect_phase**: child_a → child_b → parent → test (아래에서 위)
> 3. **run_phase**: 모든 컴포넌트가 동시 시작 (@ 0), test만 #10 후 완료

---

## 4.4 종합: UVM 컴포넌트 작성 패턴

> **이 절의 목표**: 지금까지 배운 내용을 종합하여, UVM 컴포넌트를 작성할 때의 표준 패턴을 정리합니다.

### 4.4.1 UVM 컴포넌트 작성 템플릿

모든 UVM 컴포넌트는 이 패턴을 따릅니다:

```systemverilog
class 클래스이름 extends 부모_UVM_클래스;
  // 1. Factory 등록
  `uvm_component_utils(클래스이름)

  // 2. 하위 컴포넌트 핸들 선언
  하위컴포넌트_타입 핸들이름;

  // 3. 표준 생성자
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  // 4. build_phase: 하위 컴포넌트 생성
  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    핸들이름 = 하위컴포넌트_타입::type_id::create("이름", this);
  endfunction

  // 5. connect_phase: 포트 연결 (Chapter 7에서 배움)
  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    // 연결 코드
  endfunction

  // 6. run_phase: 시뮬레이션 로직 (필요한 경우만)
  virtual task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    // 시뮬레이션 코드
    phase.drop_objection(this);
  endtask
endclass
```

### 4.4.2 uvm_object 작성 템플릿

데이터 클래스(트랜잭션 등)는 이 패턴을 따릅니다:

```systemverilog
class 클래스이름 extends uvm_sequence_item;
  // 1. Factory 등록 (object용!)
  `uvm_object_utils(클래스이름)

  // 2. 데이터 필드 선언
  rand bit [7:0] addr;
  rand bit [31:0] data;

  // 3. 제약 조건
  constraint addr_c {
    addr inside {[0:255]};
  }

  // 4. 표준 생성자
  function new(string name = "클래스이름");
    super.new(name);
  endfunction

  // 5. 문자열 변환 (디버깅용)
  virtual function string convert2string();
    return $sformatf("addr=0x%02h, data=0x%08h", addr, data);
  endfunction
endclass
```

### 4.4.3 종합 실습: 미니 검증 환경

지금까지 배운 모든 것을 합쳐서 미니 검증 환경을 만들어봅시다. 아직 DUT 연결 없이 **구조만** 만드는 것이 목표입니다:

**[예제 4-4] 미니 UVM 환경 구조**

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 4-4] 미니 UVM 검증 환경 구조
// 목적: test → env → agent → (driver, monitor) 트리 구조 만들기
// DUT 연결 없이 구조만 확인

`include "uvm_macros.svh"
import uvm_pkg::*;

// ── 트랜잭션 (uvm_object) ──
class simple_txn extends uvm_sequence_item;
  `uvm_object_utils(simple_txn)

  rand bit [7:0]  addr;
  rand bit [31:0] data;
  rand bit        rw;     // 0: Read, 1: Write

  constraint addr_c { addr inside {[0:127]}; }
  constraint rw_c   { rw dist {0 := 3, 1 := 7}; }  // 쓰기 70%

  function new(string name = "simple_txn");
    super.new(name);
  endfunction

  virtual function string convert2string();
    return $sformatf("addr=0x%02h, data=0x%08h, %s",
                     addr, data, rw ? "WR" : "RD");
  endfunction
endclass

// ── 드라이버 (uvm_component) ──
class simple_driver extends uvm_component;
  `uvm_component_utils(simple_driver)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    `uvm_info(get_type_name(), "드라이버 생성 완료", UVM_MEDIUM)
  endfunction

  virtual task run_phase(uvm_phase phase);
    `uvm_info(get_type_name(), "드라이버 대기 중... (Chapter 7에서 구현)", UVM_MEDIUM)
  endtask
endclass

// ── 모니터 (uvm_component) ──
class simple_monitor extends uvm_component;
  `uvm_component_utils(simple_monitor)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    `uvm_info(get_type_name(), "모니터 생성 완료", UVM_MEDIUM)
  endfunction

  virtual task run_phase(uvm_phase phase);
    `uvm_info(get_type_name(), "모니터 관찰 중... (Chapter 7에서 구현)", UVM_MEDIUM)
  endtask
endclass

// ── 에이전트 (uvm_component) ──
class simple_agent extends uvm_agent;
  `uvm_component_utils(simple_agent)

  simple_driver  drv;
  simple_monitor mon;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    drv = simple_driver::type_id::create("drv", this);
    mon = simple_monitor::type_id::create("mon", this);
    `uvm_info(get_type_name(), "에이전트: 드라이버 + 모니터 생성", UVM_MEDIUM)
  endfunction
endclass

// ── 환경 (uvm_component) ──
class simple_env extends uvm_env;
  `uvm_component_utils(simple_env)

  simple_agent agent;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    agent = simple_agent::type_id::create("agent", this);
    `uvm_info(get_type_name(), "환경: 에이전트 생성", UVM_MEDIUM)
  endfunction
endclass

// ── 테스트 (최상위) ──
class mini_test extends uvm_test;
  `uvm_component_utils(mini_test)

  simple_env env;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = simple_env::type_id::create("env", this);
    `uvm_info(get_type_name(), "테스트: 환경 생성", UVM_MEDIUM)
  endfunction

  virtual task run_phase(uvm_phase phase);
    simple_txn txn;
    phase.raise_objection(this);

    `uvm_info(get_type_name(), "=== 미니 검증 환경 가동! ===", UVM_MEDIUM)

    // 트랜잭션 3개 생성하여 출력
    repeat(3) begin
      txn = simple_txn::type_id::create("txn");
      if (!txn.randomize())
        `uvm_fatal(get_type_name(), "랜덤화 실패!")
      `uvm_info(get_type_name(),
        $sformatf("생성된 트랜잭션: %s", txn.convert2string()), UVM_MEDIUM)
    end

    // 컴포넌트 트리 출력 (UVM 내장 기능)
    `uvm_info(get_type_name(), "=== 컴포넌트 트리 ===", UVM_MEDIUM)
    uvm_top.print_topology();

    phase.drop_objection(this);
  endtask
endclass

module top;
  initial begin
    run_test("mini_test");
  end
endmodule
```

**예상 출력**:
```
UVM_INFO @ 0: uvm_test_top [mini_test] 테스트: 환경 생성
UVM_INFO @ 0: uvm_test_top.env [simple_env] 환경: 에이전트 생성
UVM_INFO @ 0: uvm_test_top.env.agent [simple_agent] 에이전트: 드라이버 + 모니터 생성
UVM_INFO @ 0: uvm_test_top.env.agent.drv [simple_driver] 드라이버 생성 완료
UVM_INFO @ 0: uvm_test_top.env.agent.mon [simple_monitor] 모니터 생성 완료
UVM_INFO @ 0: uvm_test_top [mini_test] === 미니 검증 환경 가동! ===
UVM_INFO @ 0: uvm_test_top [mini_test] 생성된 트랜잭션: addr=0x1a, data=0x3f2c80a4, WR
UVM_INFO @ 0: uvm_test_top [mini_test] 생성된 트랜잭션: addr=0x42, data=0x0000beef, RD
UVM_INFO @ 0: uvm_test_top [mini_test] 생성된 트랜잭션: addr=0x05, data=0x12345678, WR
UVM_INFO @ 0: uvm_test_top [mini_test] === 컴포넌트 트리 ===

--------------------------------------
Name          Type           Size  Value
--------------------------------------
uvm_test_top  mini_test      -     @...
  env         simple_env     -     @...
    agent     simple_agent   -     @...
      drv     simple_driver  -     @...
      mon     simple_monitor -     @...
--------------------------------------
```

> **관찰 포인트**:
> 1. build_phase 실행 순서: test → env → agent → drv, mon (위에서 아래)
> 2. 컴포넌트 경로: `uvm_test_top.env.agent.drv` — 트리 구조가 명확합니다
> 3. `print_topology()`로 전체 구조를 한눈에 확인할 수 있습니다
> 4. 트랜잭션은 랜덤화로 매번 다른 값이 생성됩니다

> **성취감 포인트**: 축하합니다! 방금 실무에서 사용하는 것과 동일한 구조의 UVM 검증 환경 뼈대를 만들었습니다. test → env → agent → driver/monitor — 이 구조를 기반으로 Chapter 5에서 첫 완전한 테스트벤치를 만들게 됩니다.

---

## 4.5 체크포인트

### 셀프 체크

아래 질문에 답할 수 있다면 이 챕터를 충분히 이해한 것입니다:

1. `uvm_object`와 `uvm_component`의 가장 큰 차이점 2가지는?

<details>
<summary>정답 확인</summary>

(1) uvm_component는 부모-자식 관계(트리 구조)가 있지만 uvm_object는 없습니다.
(2) uvm_component는 Phase(build, connect, run)가 있지만 uvm_object는 없습니다.
추가: uvm_component의 생성자에는 parent 파라미터가 필요합니다.
</details>

2. UVM에서 `new()` 대신 `type_id::create()`를 사용하는 이유는?

<details>
<summary>정답 확인</summary>

Factory 패턴을 통해 코드 수정 없이 컴포넌트를 교체할 수 있게 하기 위해서입니다. 예를 들어, 기본 드라이버를 에러 주입 드라이버로 교체할 때, create()를 사용했으면 테스트 클래스에서 set_type_override() 한 줄로 교체 가능하지만, new()를 사용했으면 환경 코드를 직접 수정해야 합니다.
</details>

3. `` `uvm_component_utils ``와 `` `uvm_object_utils ``는 각각 언제 사용하는가?

<details>
<summary>정답 확인</summary>

`uvm_component_utils`는 uvm_component를 상속한 클래스(test, env, agent, driver, monitor 등)에 사용합니다.
`uvm_object_utils`는 uvm_object를 상속한 클래스(transaction, sequence 등)에 사용합니다.
둘 다 Factory에 클래스를 등록하여 type_id::create()로 생성할 수 있게 해줍니다.
</details>

4. build_phase, connect_phase, run_phase의 실행 순서와 각각의 역할은?

<details>
<summary>정답 확인</summary>

실행 순서: build_phase → connect_phase → run_phase
- build_phase: 하위 컴포넌트를 create()로 생성하는 단계. 위에서 아래로(Top-Down) 실행
- connect_phase: 포트를 연결하는 단계. 아래에서 위로(Bottom-Up) 실행
- run_phase: 실제 시뮬레이션이 동작하는 단계. 모든 컴포넌트가 동시 실행. task이므로 시간 소모 가능 (#, @)
</details>

5. `raise_objection()`과 `drop_objection()`은 왜 필요한가?

<details>
<summary>정답 확인</summary>

run_phase에서 시뮬레이션의 종료 시점을 제어하기 위해서입니다. raise_objection은 "아직 할 일이 남았으니 종료하지 마세요"이고, drop_objection은 "할 일을 마쳤습니다"입니다. 아무도 raise하지 않으면 UVM은 할 일이 없다고 판단하여 즉시 종료합니다.
</details>

6. build_phase가 Top-Down으로 실행되는 이유는?

<details>
<summary>정답 확인</summary>

부모 컴포넌트가 먼저 생성되어야 자식 컴포넌트를 만들 수 있기 때문입니다. 예를 들어, env의 build_phase에서 agent를 create()하므로, env가 먼저 build되어야 agent를 만들 수 있습니다. 반면 connect_phase는 아래에서 위로(Bottom-Up) 실행됩니다 — 자식이 먼저 준비되어야 부모가 연결할 수 있으니까요.
</details>

### 연습문제

**[실습 4-1] 컴포넌트 추가하기 (쉬움)** — 약 10분

[예제 4-4]의 `simple_agent`에 `simple_sequencer`(uvm_sequencer를 extends) 컴포넌트를 추가하세요. build_phase에서 생성하고, 출력에서 컴포넌트 트리에 나타나는지 확인하세요.

<details>
<summary>힌트</summary>

`class simple_sequencer extends uvm_sequencer;`로 만들고, agent의 build_phase에서 `sqr = simple_sequencer::type_id::create("sqr", this);`로 생성합니다.
</details>

<details>
<summary>모범 답안</summary>

```systemverilog
// simple_monitor 클래스 아래에 추가
class simple_sequencer extends uvm_sequencer;
  `uvm_component_utils(simple_sequencer)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    `uvm_info(get_type_name(), "시퀀서 생성 완료", UVM_MEDIUM)
  endfunction
endclass

// simple_agent 클래스 수정
class simple_agent extends uvm_agent;
  `uvm_component_utils(simple_agent)

  simple_driver    drv;
  simple_monitor   mon;
  simple_sequencer sqr;  // 추가!

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    drv = simple_driver::type_id::create("drv", this);
    mon = simple_monitor::type_id::create("mon", this);
    sqr = simple_sequencer::type_id::create("sqr", this);  // 추가!
    `uvm_info(get_type_name(), "에이전트: 드라이버 + 모니터 + 시퀀서 생성", UVM_MEDIUM)
  endfunction
endclass
```
</details>

**[실습 4-2] 트랜잭션 확장하기 (보통)** — 약 15분

`simple_txn`을 상속하여 `error_txn` 클래스를 만드세요. `rand bit inject_error` 필드를 추가하고, `convert2string()`을 오버라이드하여 에러 여부도 출력되게 하세요. `mini_test`의 run_phase에서 `error_txn`을 생성하여 출력하세요.

<details>
<summary>힌트</summary>

`class error_txn extends simple_txn;`로 시작하고, `` `uvm_object_utils(error_txn) ``를 사용합니다. 생성은 `error_txn::type_id::create("txn")`으로 합니다.
</details>

<details>
<summary>모범 답안</summary>

```systemverilog
class error_txn extends simple_txn;
  `uvm_object_utils(error_txn)

  rand bit inject_error;

  constraint error_c {
    inject_error dist { 1 := 2, 0 := 8 };  // 20% 에러 주입
  }

  function new(string name = "error_txn");
    super.new(name);
  endfunction

  virtual function string convert2string();
    string base_str = super.convert2string();
    return $sformatf("%s, error=%s", base_str,
                     inject_error ? "YES" : "NO");
  endfunction
endclass

// mini_test의 run_phase에서:
error_txn etxn;
repeat(5) begin
  etxn = error_txn::type_id::create("etxn");
  if (!etxn.randomize())
    `uvm_fatal(get_type_name(), "랜덤화 실패!")
  `uvm_info(get_type_name(),
    $sformatf("에러 트랜잭션: %s", etxn.convert2string()), UVM_MEDIUM)
end
```
</details>

**[실습 4-3] Phase 순서 예측 (도전)** — 약 10분

아래 구조에서 build_phase와 connect_phase의 실행 순서를 예측하세요:

```
test
  ├── env1
  │    └── agent_a
  │         ├── drv_a
  │         └── mon_a
  └── env2
       └── agent_b
            └── drv_b
```

<details>
<summary>정답 확인</summary>

**build_phase (Top-Down)**:
1. test
2. env1
3. agent_a
4. drv_a
5. mon_a
6. env2
7. agent_b
8. drv_b

**connect_phase (Bottom-Up)**:
1. drv_a
2. mon_a
3. agent_a
4. env1
5. drv_b
6. agent_b
7. env2
8. test

참고: 같은 레벨의 형제 컴포넌트(env1과 env2, drv_a와 mon_a)의 순서는 생성 순서에 따라 달라질 수 있지만, 부모-자식 간의 Top-Down/Bottom-Up 원칙은 항상 유지됩니다.
</details>

### 흔한 에러와 해결법

| 에러 메시지 | 원인 | 해결 |
|------------|------|------|
| `UVM_FATAL ... [NOFACTORY]` | `uvm_component_utils` 또는 `uvm_object_utils` 누락 | class 다음 줄에 매크로 추가 |
| `Bad handle or reference (SIGSEGV)` | create() 없이 컴포넌트 사용 | build_phase에서 create()로 생성 |
| run_phase가 즉시 종료 | raise_objection() 누락 | run_phase 시작 시 raise_objection() 추가 |
| `connect_phase에서 null 참조` | build_phase에서 create() 안 함 | build_phase에서 먼저 생성 확인 |
| `uvm_component_utils 대신 uvm_object_utils 사용` | component에 object 매크로 사용 | 클래스가 상속한 부모 확인 후 올바른 매크로 선택 |

### 용어 정리

| 한글 용어 | 영어 | 설명 |
|-----------|------|------|
| 팩토리 | Factory | 객체 생성을 관리하는 메커니즘. type_id::create()로 사용 |
| 페이즈 | Phase | 시뮬레이션 단계를 관리하는 메커니즘. build → connect → run |
| 컴포넌트 | Component | 테스트벤치의 구조를 이루는 클래스 (uvm_component 상속) |
| 오브젝트 | Object | 데이터를 담는 클래스 (uvm_object 상속) |
| 컴포넌트 트리 | Component Tree | 부모-자식 관계로 이루어진 테스트벤치 계층 구조 |
| 오브젝션 | Objection | run_phase 종료 시점을 제어하는 메커니즘 |
| 매크로 | Macro | 컴파일러가 전처리하는 코드 치환. `uvm_component_utils 등 |
| 토폴로지 | Topology | 컴포넌트 트리의 전체 구조. print_topology()로 출력 |
| 오버라이드 | Override | Factory를 통해 한 클래스를 다른 클래스로 교체하는 기능 |

### 다음 챕터 미리보기

> Chapter 5에서는 다음 내용을 학습합니다:
> - 실제 DUT(간단한 카운터)와 연결하는 완전한 UVM 테스트벤치 구축
> - `uvm_config_db`로 설정값을 전달하는 방법
> - Virtual Interface를 통한 DUT-테스트벤치 연결
> - 첫 번째 **완전한** 시뮬레이션 실행
>
> 이 챕터에서 만든 test → env → agent → driver/monitor 구조가 Chapter 5의 기반입니다!
