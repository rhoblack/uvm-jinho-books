# Chapter 2: 환경 설정

> **학습 목표**
> - EDA 시뮬레이터의 종류와 역할을 이해한다
> - EDA Playground에서 UVM 코드를 작성하고 실행한다
> - 로컬 환경에서 시뮬레이터와 UVM 라이브러리를 설정한다 (선택)
> - UVM 프로젝트의 표준 디렉토리 구조를 익힌다
> - 첫 UVM "Hello World" 프로그램을 컴파일하고 실행한다

---

## 2.1 시뮬레이터란 무엇인가?

### 2.1.1 시뮬레이터의 역할

Chapter 1에서 UVM이 검증 방법론이라는 것을 배웠습니다. 그런데 UVM 코드를 작성한다고 해서 바로 실행할 수 있는 것은 아닙니다. **시뮬레이터(Simulator)**가 필요합니다.

```
일반 프로그래밍:  C코드 → gcc(컴파일러) → 실행파일 → 실행
UVM 검증:        SV코드 → 시뮬레이터(컴파일+실행) → 검증 결과
```

시뮬레이터는 SystemVerilog 코드를 **컴파일**하고 **시뮬레이션**하는 도구입니다. C 프로그래밍에서 gcc가 하는 역할과 비슷하다고 생각하면 됩니다.

> **핵심**: UVM을 배우려면 반드시 SystemVerilog를 지원하는 시뮬레이터가 필요합니다. 시뮬레이터 없이는 코드를 실행할 수 없습니다.

### 2.1.2 주요 상용 시뮬레이터

반도체 업계에서 사용하는 3대 시뮬레이터가 있습니다:

| 시뮬레이터 | 제조사 | 특징 |
|-----------|--------|------|
| **VCS** | Synopsys | 업계 점유율 1위, 가장 빠른 컴파일 속도 |
| **Questa** | Siemens EDA | 강력한 디버깅 기능, UVM 라이브러리 내장 |
| **Xcelium** | Cadence | 멀티코어 시뮬레이션, 대규모 설계에 강점 |

> **현실적인 이야기**: 이 시뮬레이터들은 모두 **상용 라이선스**가 필요하고, 가격이 수천만 원에 달합니다. 회사에 입사하면 사용할 수 있지만, 학습 단계에서는 접근이 어렵습니다.

그래서 이 책에서는 **무료로 사용할 수 있는 방법**을 먼저 안내합니다.

### 2.1.3 무료 실습 환경 선택지

초보자가 UVM을 연습할 수 있는 환경은 크게 3가지입니다:

| 환경 | 비용 | 설치 | UVM 지원 | 추천 대상 |
|------|------|------|---------|-----------|
| **EDA Playground** | 무료 | 불필요 (웹) | O (Questa/VCS/Xcelium 선택 가능) | **모든 초보자 (추천)** |
| **Questa (Intel FPGA Edition)** | 무료 | 필요 | O (제한적) | 로컬 환경을 원하는 분 |
| **Icarus Verilog + Verilator** | 무료 | 필요 | X (UVM 미지원) | Verilog만 연습할 때 |

> **참고**: UVM에는 두 가지 주요 버전이 있습니다. **UVM 1.2**는 Accellera에서 만든 버전이고, **UVM 1800.2**는 IEEE 표준으로 채택된 버전입니다. 둘은 거의 동일하며, EDA Playground에서는 주로 UVM 1.2를 선택합니다.

> **이 책의 선택**: Part 1(시작하기) 전체를 **EDA Playground**로 실습합니다. 웹 브라우저만 있으면 되므로 설치 없이 바로 시작할 수 있습니다. 로컬 환경 설정은 이 챕터 뒷부분에서 선택 사항으로 안내합니다.

---

## 2.2 EDA Playground로 바로 시작하기

> **이 절의 목표**: EDA Playground에서 첫 UVM 코드를 실행하고, 출력 결과를 읽을 수 있게 됩니다.

### 2.2.1 EDA Playground란?

EDA Playground(https://www.edaplayground.com)는 웹 브라우저에서 SystemVerilog와 UVM 코드를 작성하고 실행할 수 있는 **무료 온라인 시뮬레이션 환경**입니다.

**장점**:
- 설치 불필요 (웹 브라우저만 있으면 됨)
- Questa, VCS, Xcelium 등 상용 시뮬레이터를 무료로 사용 가능
- UVM 라이브러리가 이미 설정되어 있음
- 코드를 저장하고 공유 가능 (Save 버튼으로 저장, URL로 공유)

```
┌──────────────────────────────────────────────────────────┐
│  [Languages & Libraries ▼]  [Tools & Simulators ▼]  [Run] │
├──────────────────────────┬───────────────────────────────┤
│   testbench.sv           │    design.sv                  │
│   (왼쪽 패널)             │    (오른쪽 패널 - 비워둠)      │
│   여기에 UVM 코드 작성     │                               │
│                          │                               │
├──────────────────────────┴───────────────────────────────┤
│   Log (실행 결과)                                         │
└──────────────────────────────────────────────────────────┘
```

### 2.2.2 EDA Playground 설정 확인

Chapter 1에서 이미 EDA Playground 계정을 만들고 첫 코드를 실행해보았습니다. 같은 계정으로 로그인한 후, 이번 챕터의 실습을 위해 설정을 확인합니다:

1. https://www.edaplayground.com 에 로그인
2. 좌측 패널 상단에서:
   - **"Languages & Libraries"** → `SystemVerilog/Verilog` 선택
   - **"UVM/OVM"** → `UVM 1.2` 선택
3. 상단 툴바에서:
   - **"Tools & Simulators"** → Chapter 1에서 선택한 시뮬레이터를 그대로 사용하세요. 어떤 시뮬레이터를 선택해도 UVM 코드의 동작은 동일합니다.

> **팁**: 계정이 없다면 Chapter 1의 1.3.2절을 참고하여 만들어주세요. Google 계정으로 간편 로그인도 가능합니다.

### 2.2.3 첫 UVM 코드 실행하기 (10분)

Chapter 1에서 간단한 UVM 코드를 실행해본 적이 있습니다. 이번에는 한 단계 더 나아가서, 코드의 각 부분이 어떤 역할을 하는지 주석으로 상세히 설명한 버전을 작성합니다.

> **코드를 다 이해할 필요 없습니다!** 지금은 "이 코드를 실행하면 UVM이 동작한다"는 것만 확인하세요. `class`, `extends`, `phase` 같은 용어는 Chapter 3~5에서 하나씩 배웁니다.

**[예제 2-1] UVM Hello World**

왼쪽 패널(testbench.sv)에 아래 코드를 입력하세요:

```systemverilog
// 파일: testbench.sv
// 설명: 첫 UVM Hello World 프로그램
// 역할: UVM 환경이 정상 동작하는지 확인

// UVM 라이브러리 가져오기
// (C에서 #include <stdio.h> 하는 것과 같습니다)
`include "uvm_macros.svh"
import uvm_pkg::*;

// 가장 간단한 UVM 테스트 클래스
class hello_test extends uvm_test;
  // 팩토리(Factory)에 등록
  // → run_test()가 이 클래스를 이름으로 찾으려면, 여기에 등록되어 있어야 합니다.
  //   등록하지 않으면 "클래스를 찾을 수 없다"는 에러가 발생합니다.
  `uvm_component_utils(hello_test)

  // 생성자 (모든 UVM 컴포넌트에 필요합니다)
  // parent: UVM은 컴포넌트를 트리(나무) 구조로 관리합니다.
  //         부모 컴포넌트를 지정하는 매개변수입니다. (Chapter 4에서 자세히 배웁니다)
  function new(string name = "hello_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  // 시뮬레이션 실행 단계
  // task: function과 달리 시간 지연(#delay)을 사용할 수 있습니다.
  //       run_phase는 시뮬레이션 시간이 흐르므로 task로 선언합니다.
  virtual task run_phase(uvm_phase phase);
    // 오브젝션(Objection): "아직 할 일이 있어요!" 라고 UVM에 알려주는 것
    // UVM은 여러 컴포넌트가 동시에 돌아가기 때문에,
    // 아무도 오브젝션을 올리지 않으면 "모두 할 일이 없다"고 판단하여 종료합니다.
    phase.raise_objection(this);

    // UVM 메시지 출력 (일반 $display 대신 사용)
    `uvm_info("HELLO", "첫 번째 UVM 프로그램이 실행되었습니다!", UVM_LOW)
    `uvm_info("HELLO", "UVM 환경 설정 성공! 다음 챕터로 넘어갈 준비 완료!", UVM_LOW)

    // 잠시 시뮬레이션 시간 진행 (100ns)
    #100;

    // 오브젝션 해제: "할 일 끝났습니다"
    phase.drop_objection(this);
  endtask
endclass

// 최상위 모듈 (시뮬레이션 시작점)
module top;
  initial begin
    // UVM 테스트 실행 - hello_test 클래스를 팩토리에서 찾아서 시작합니다
    run_test("hello_test");
  end
endmodule
```

상단의 **"Run"** 버튼을 클릭하여 실행합니다 (또는 Ctrl+Enter).

**예상 출력**:
```
UVM_INFO testbench.sv(28) @ 0: uvm_test_top [HELLO] 첫 번째 UVM 프로그램이 실행되었습니다!
UVM_INFO testbench.sv(29) @ 0: uvm_test_top [HELLO] UVM 환경 설정 성공! 다음 챕터로 넘어갈 준비 완료!

--- UVM Report Summary ---
** Report counts by severity
UVM_INFO :    4
UVM_WARNING :    0
UVM_ERROR :    0
UVM_FATAL :    0
** Report counts by id
[HELLO]     2
...
```

> **참고**: 출력에 표시되는 줄 번호(예: `testbench.sv(28)`)는 시뮬레이터와 코드 붙여넣기 방식에 따라 다를 수 있습니다. 메시지 내용이 동일하면 정상입니다.

### 2.2.4 출력 결과 해석하기

위 출력에서 각 부분이 무엇을 의미하는지 알아봅시다. Chapter 1에서 이미 출력 형식을 배웠는데, 여기서는 **Report Summary** 읽는 법에 집중합니다:

```
UVM_INFO testbench.sv(28) @ 0: uvm_test_top [HELLO] 메시지 내용
   │          │          │        │           │         │
   │          │          │        │           │         └─ 출력 메시지
   │          │          │        │           └─ 메시지 태그 (분류용)
   │          │          │        └─ 컴포넌트 경로 (어디서 출력했는지)
   │          │          └─ 시뮬레이션 시간 (0ns 시점)
   │          └─ 파일명과 줄 번호
   └─ 메시지 심각도 (INFO/WARNING/ERROR/FATAL)
```

**Report Summary 읽는 법**:

시뮬레이션이 끝나면 UVM이 자동으로 요약 보고서를 출력합니다:

```
--- UVM Report Summary ---
** Report counts by severity      ← 심각도별 메시지 개수
UVM_INFO :    4                    ← INFO 메시지 4개 (시스템 메시지 포함)
UVM_WARNING :    0                 ← 경고 없음
UVM_ERROR :    0                   ← 에러 없음 ✓
UVM_FATAL :    0                   ← 치명적 에러 없음 ✓
```

> **핵심**: `UVM_ERROR: 0`, `UVM_FATAL: 0`이면 시뮬레이션이 정상 종료된 것입니다. 이 두 줄만 확인하면 됩니다.

### 2.2.5 자주 발생하는 에러와 해결법

#### 에러 1: UVM 라이브러리를 못 찾는 경우
```
** Error: testbench.sv(2): `include "uvm_macros.svh" - file not found
```
**원인**: EDA Playground에서 UVM 라이브러리를 선택하지 않았습니다.
**해결**: 좌측 패널 → "UVM/OVM" → `UVM 1.2` 선택

#### 에러 2: 팩토리(Factory) 등록 누락
```
UVM_FATAL @ 0: reporter [INVTST] Requested test from call to run_test(hello_test) not found.
```
**원인**: `` `uvm_component_utils(hello_test) `` 매크로를 빠뜨렸습니다. `run_test()`가 팩토리에서 클래스를 찾으려고 했지만, 등록되어 있지 않아서 실패한 것입니다.
**해결**: class 선언 바로 다음 줄에 매크로 추가

#### 에러 3: 시뮬레이션이 바로 끝나는 경우
```
UVM_INFO ... @ 0: uvm_test_top [HELLO] ... (시간 지연 이후의 메시지가 출력되지 않음)
```
**원인**: `phase.raise_objection(this)`를 빠뜨렸습니다. UVM은 아무도 오브젝션을 올리지 않으면 "할 일이 없다"고 판단하여 run_phase를 즉시 종료합니다. 그 결과 `#100` 이후에 배치된 코드는 실행되지 않습니다.
**해결**: run_phase 시작 부분에 `raise_objection` 추가, 끝에 `drop_objection` 추가

이제 EDA Playground에서 코드를 성공적으로 실행했습니다. 다음으로, 방금 실행한 UVM 코드의 구조를 하나씩 뜯어봅시다.

---

## 2.3 UVM 코드 구조 이해하기

> **이 절의 목표**: UVM 프로그램의 3가지 필수 요소(라이브러리, 컴포넌트, 시작점)를 구분할 수 있게 됩니다.

### 2.3.1 UVM 프로그램의 기본 뼈대

모든 UVM 프로그램은 아래 3가지 요소를 반드시 포함합니다:

```systemverilog
// === 1. UVM 라이브러리 가져오기 (필수) ===
`include "uvm_macros.svh"   // UVM 매크로 정의 파일
import uvm_pkg::*;           // UVM 패키지의 모든 클래스 가져오기

// === 2. UVM 컴포넌트 정의 (테스트 클래스) ===
class my_test extends uvm_test;
  `uvm_component_utils(my_test)       // 팩토리(Factory) 등록
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
  // ... 테스트 내용 ...
endclass

// === 3. 시뮬레이션 시작점 ===
module top;
  initial begin
    run_test("my_test");              // 테스트 실행
  end
endmodule
```

각 부분의 역할을 정리하면:

| 부분 | 코드 | 비유 |
|------|------|------|
| 라이브러리 가져오기 | `` `include ``, `import` | 요리하기 전에 재료와 도구 준비 |
| 컴포넌트 정의 | `class ... extends ...` | 레시피(어떻게 검증할지) 작성 |
| 시작점 | `run_test()` | "요리 시작!" 버튼 누르기 |

### 2.3.2 `include`와 `import`의 차이

초보자가 자주 헷갈리는 부분입니다:

```systemverilog
`include "uvm_macros.svh"   // 전처리기 지시자: 파일 내용을 그대로 복사/붙여넣기
import uvm_pkg::*;           // SystemVerilog 패키지: 클래스/함수를 사용 가능하게 등록
```

| 비교 | `` `include `` | `import` |
|------|----------|---------|
| 역할 | 파일 내용을 복사 | 패키지 안의 클래스/함수를 사용 가능하게 함 |
| C 비유 | `#include <header.h>` | `using namespace std;` (패키지 안의 모든 것을 사용하겠다는 선언) |
| 없으면 | 매크로 사용 불가 | UVM 클래스 사용 불가 |
| 순서 | **반드시 import보다 먼저** | `include` 다음에 |

> **주의**: `` `include ``를 `import`보다 먼저 써야 합니다. 순서가 바뀌면 컴파일 에러가 발생합니다.

### 2.3.3 `uvm_info` vs `$display` 비교

Chapter 1에서 `uvm_info` 매크로를 배웠습니다. 여기서는 기존의 `$display`와 비교하여, 왜 UVM에서는 `uvm_info`를 사용하는지 집중적으로 알아봅니다:

```systemverilog
// 전통적 방식 (비추천)
$display("Hello World");

// UVM 방식 (추천)
`uvm_info("TAG", "Hello World", UVM_LOW)
//          │        │             │
//          │        │             └─ 출력 상세 수준(Verbosity): LOW=항상 출력
//          │        └─ 출력할 메시지
//          └─ 메시지 태그 (로그 필터링에 사용)
```

**왜 `$display` 대신 `uvm_info`를 쓸까요?**

| 기능 | `$display` | `` `uvm_info `` |
|------|-----------|-------------|
| 파일/줄 번호 | X | O (자동 포함) |
| 시뮬레이션 시간 | X | O (자동 포함) |
| 컴포넌트 위치 | X | O (어느 컴포넌트에서 출력했는지) |
| 필터링 | X | O (출력 상세 수준별 표시/숨기기 가능) |
| 리포트 요약 | X | O (끝에 자동 요약) |

> **실무 팁**: 회사에서 `$display`를 쓰면 코드 리뷰에서 지적받습니다. 처음부터 `uvm_info` 사용을 습관화하세요.

**출력 상세 수준(Verbosity)**:

Chapter 1에서 소개한 출력 상세 수준을 다시 정리합니다:

```systemverilog
`uvm_info("TAG", "항상 보이는 메시지", UVM_NONE)    // 중요도 0 (항상 표시)
`uvm_info("TAG", "중요한 메시지", UVM_LOW)           // 중요도 100 (기본 표시)
`uvm_info("TAG", "보통 메시지", UVM_MEDIUM)          // 중요도 200
`uvm_info("TAG", "상세 메시지", UVM_HIGH)            // 중요도 300
`uvm_info("TAG", "최상세 메시지", UVM_FULL)          // 중요도 400
`uvm_info("TAG", "디버깅용 메시지", UVM_DEBUG)       // 중요도 500 (디버깅 시만)
```

시뮬레이션 실행 시 출력 상세 수준을 조절하면, 필요한 메시지만 골라서 볼 수 있습니다. 이 기능은 Chapter 10(디버깅 기법)에서 자세히 다룹니다.

UVM 코드의 기본 구조를 이해했으니, 이제 직접 코드를 수정하면서 체험해봅시다.

---

## 2.4 실습: UVM 코드 수정해보기

> **이 절의 목표**: UVM 코드를 직접 수정하고 실행하면서, 메시지 출력과 페이즈(Phase) 동작을 체험합니다.

### 2.4.1 실습 1: 메시지 바꿔보기 (쉬움)

**[예제 2-2] 메시지 변경 실습**

Hello World 코드에서 메시지를 수정하고 실행해보세요.

```systemverilog
// 파일: testbench.sv
// [예제 2-2] 메시지 변경 실습

`include "uvm_macros.svh"
import uvm_pkg::*;

class hello_test extends uvm_test;
  `uvm_component_utils(hello_test)

  function new(string name = "hello_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual task run_phase(uvm_phase phase);
    phase.raise_objection(this);

    // 아래 메시지를 자유롭게 바꿔보세요!
    `uvm_info("MY_TAG", "나의 첫 UVM 메시지입니다!", UVM_LOW)

    // 다른 심각도도 실험해보세요
    `uvm_warning("MY_TAG", "이것은 경고 메시지입니다")
    `uvm_error("MY_TAG", "이것은 에러 메시지입니다")

    #100;
    phase.drop_objection(this);
  endtask
endclass

module top;
  initial begin
    run_test("hello_test");
  end
endmodule
```

**실행 후 확인사항**:
- UVM Report Summary에서 WARNING과 ERROR 카운트가 증가했나요?
- `uvm_error`를 10개 이상 넣으면 어떻게 되나요? (직접 해보세요!)

> **참고**: `uvm_error`는 이 실습에서 실험 목적으로 사용한 것입니다. 실제 코드에서는 에러가 없는 것이 정상입니다. UVM은 기본적으로 에러가 10개 누적되면 시뮬레이션을 자동 중단합니다.

### 2.4.2 실습 2: 여러 페이즈(Phase) 체험하기 (보통)

UVM에는 run_phase 외에도 여러 페이즈(Phase)가 있습니다. Chapter 1에서 9개의 페이즈를 소개했는데, 이번 실습에서는 그 중 가장 핵심적인 4개를 직접 체험합니다. 나머지 페이즈도 동일한 순서 규칙에 따라 실행됩니다.

**[예제 2-3] 페이즈(Phase) 순서 확인**

```systemverilog
// 파일: testbench.sv
// [예제 2-3] UVM 페이즈(Phase) 순서 확인
// 각 페이즈가 어떤 순서로 실행되는지 직접 확인합니다

`include "uvm_macros.svh"
import uvm_pkg::*;

class phase_test extends uvm_test;
  `uvm_component_utils(phase_test)

  function new(string name = "phase_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  // === Build Phase: 컴포넌트 생성 단계 ===
  // function: 시간 지연 없이 즉시 완료되는 동작 (시뮬레이션 시간이 흐르지 않음)
  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    `uvm_info("PHASE", "[1] build_phase - 컴포넌트를 만드는 단계", UVM_LOW)
  endfunction

  // === Connect Phase: 컴포넌트 연결 단계 ===
  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    `uvm_info("PHASE", "[2] connect_phase - 컴포넌트를 서로 연결하는 단계", UVM_LOW)
  endfunction

  // === Run Phase: 실제 시뮬레이션 단계 ===
  // task: 시간 지연(#delay)을 사용할 수 있음 (시뮬레이션 시간이 흐름)
  virtual task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    `uvm_info("PHASE", "[3] run_phase - 시뮬레이션 실행 중!", UVM_LOW)
    #100;
    phase.drop_objection(this);
  endtask

  // === Report Phase: 결과 보고 단계 ===
  virtual function void report_phase(uvm_phase phase);
    super.report_phase(phase);
    `uvm_info("PHASE", "[4] report_phase - 결과를 정리하는 단계", UVM_LOW)
  endfunction
endclass

module top;
  initial begin
    run_test("phase_test");
  end
endmodule
```

**예상 출력 순서**:
```
UVM_INFO ... [PHASE] [1] build_phase - 컴포넌트를 만드는 단계
UVM_INFO ... [PHASE] [2] connect_phase - 컴포넌트를 서로 연결하는 단계
UVM_INFO ... [PHASE] [3] run_phase - 시뮬레이션 실행 중!
UVM_INFO ... [PHASE] [4] report_phase - 결과를 정리하는 단계
```

> **관찰**: 페이즈가 정해진 순서대로 실행됩니다. build(만들기) → connect(연결하기) → run(실행하기) → report(보고하기) — 마치 레고를 조립할 때 "부품 준비 → 조립 → 작동 테스트 → 결과 기록" 순서와 같습니다. 이 순서는 UVM이 자동으로 관리합니다. 페이즈의 자세한 내용은 Chapter 4에서 배웁니다.
>
> **function vs task**: build_phase, connect_phase, report_phase는 `function`으로 선언되어 있고, run_phase만 `task`로 선언되어 있습니다. `task`는 시간 지연(`#delay`)을 사용할 수 있기 때문입니다. run_phase 안에 `#100`이 있으므로 반드시 `task`여야 합니다.

### 2.4.3 실습 3: 반복 테스트 만들기 (보통)

같은 동작을 여러 번 반복하는 테스트를 만들어 봅시다. 실무에서는 이런 식으로 반복 테스트를 많이 합니다:

**[예제 2-4] 반복 테스트**

```systemverilog
// 파일: testbench.sv
// [예제 2-4] 반복 테스트
// for 루프를 사용하여 여러 번 테스트하는 패턴

`include "uvm_macros.svh"
import uvm_pkg::*;

class loop_test extends uvm_test;
  `uvm_component_utils(loop_test)

  function new(string name = "loop_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual task run_phase(uvm_phase phase);
    phase.raise_objection(this);

    // 5번 반복 테스트
    for (int i = 0; i < 5; i++) begin
      // $sformatf: 문자열 포맷팅 (C의 sprintf와 유사)
      `uvm_info("LOOP", $sformatf("테스트 반복 %0d/5 실행 중...", i+1), UVM_LOW)
      #10;  // 10ns 대기
    end

    `uvm_info("LOOP", "모든 반복 테스트 완료!", UVM_LOW)
    phase.drop_objection(this);
  endtask
endclass

module top;
  initial begin
    run_test("loop_test");
  end
endmodule
```

**예상 출력**:
```
UVM_INFO testbench.sv(19) @ 0: uvm_test_top [LOOP] 테스트 반복 1/5 실행 중...
UVM_INFO testbench.sv(19) @ 10: uvm_test_top [LOOP] 테스트 반복 2/5 실행 중...
UVM_INFO testbench.sv(19) @ 20: uvm_test_top [LOOP] 테스트 반복 3/5 실행 중...
UVM_INFO testbench.sv(19) @ 30: uvm_test_top [LOOP] 테스트 반복 4/5 실행 중...
UVM_INFO testbench.sv(19) @ 40: uvm_test_top [LOOP] 테스트 반복 5/5 실행 중...
UVM_INFO testbench.sv(23) @ 50: uvm_test_top [LOOP] 모든 반복 테스트 완료!
```

> **관찰**: 시뮬레이션 시간(@)이 0, 10, 20, 30, 40으로 증가합니다. `#10`이 10ns 대기를 의미하기 때문입니다.

여기까지 EDA Playground에서 충분히 실습했습니다. 더 큰 프로젝트를 위한 로컬 환경이 궁금하다면, 다음 절을 계속 읽어보세요.

---

## 2.5 로컬 환경 설정 (선택 사항)

> **Part 1(시작하기, Chapter 1~5) 전체를 EDA Playground만으로 실습할 수 있습니다.**
> 이 절은 로컬 환경을 미리 준비하고 싶은 분만 읽으세요.
> Part 2(깊이 파기)에서 로컬 환경이 필요해지면 그때 돌아와도 충분합니다.
> **지금 이 절을 건너뛰어도 학습에 전혀 지장이 없습니다. → [2.6절로 바로 이동](#26-uvm-프로젝트-디렉토리-구조)**

### 2.5.1 왜 로컬 환경이 필요할까?

EDA Playground는 편리하지만 한계가 있습니다:

| 항목 | EDA Playground | 로컬 환경 |
|------|---------------|----------|
| 파일 개수 | 제한적 (2~3개) | 무제한 |
| 시뮬레이션 시간 | 제한 (약 10초) | 무제한 |
| 파형 분석 | 제한적 | 완전한 기능 (DVE, Verdi, QuestaSim GUI 등 — Chapter 10에서 상세히 다룹니다) |
| 디버깅 | 로그만 가능 | 대화형 디버거 사용 가능 |
| 프로젝트 규모 | 작은 예제만 | 실무급 프로젝트 가능 |

### 2.5.2 운영체제 준비

반도체 업계에서는 거의 모든 작업을 **Linux**에서 합니다. Windows나 macOS를 사용하고 있다면:

| 현재 OS | 추천 방법 |
|---------|----------|
| **Linux** | 바로 사용 가능 |
| **Windows** | WSL2 (Windows Subsystem for Linux) 설치 |
| **macOS** | Docker 또는 UTM으로 Linux VM 설정 |

**WSL2 설치 (Windows 사용자)**:

```bash
# PowerShell을 관리자 권한으로 실행하고:
wsl --install

# 설치 완료 후 재부팅
# Ubuntu가 기본으로 설치됩니다
```

> **실무 팁**: 팹리스 회사에서는 주로 CentOS/RHEL 또는 Ubuntu를 사용합니다. WSL2에 Ubuntu를 설치하면 실무와 가장 비슷한 환경이 됩니다.

### 2.5.3 Questa (Intel FPGA Edition) 설치

Intel FPGA 사용자를 위해 제공되는 무료 버전으로, SystemVerilog와 UVM을 지원합니다. 참고로 이 제품은 2.1.2절에서 소개한 상용 Questa와는 별도의 제품(무료 제한판)입니다.

**설치 순서**:

1. Intel FPGA 다운로드 페이지에서 "Questa - Intel FPGA Edition" 다운로드
2. 라이선스 파일 요청 (무료, Intel 계정 필요)
3. 설치 및 환경 변수 설정:

```bash
# ~/.bashrc에 추가
export QUESTA_HOME=/opt/intelFPGA/questa_fe
export PATH=$QUESTA_HOME/bin:$PATH
export LM_LICENSE_FILE=/path/to/license.dat

# 설정 적용
source ~/.bashrc
```

4. 설치 확인:

```bash
# 버전 확인 (출력되면 설치 성공)
vsim -version
```

### 2.5.4 UVM 라이브러리 설정

상용 시뮬레이터에는 UVM 라이브러리가 내장되어 있는 경우가 많습니다. 별도 설정이 필요한 경우:

```bash
# UVM 소스 다운로드 (Accellera에서 제공)
# https://www.accellera.org/downloads/standards/uvm 에서 다운로드

# 다운로드 후 압축 해제
tar -xzf UVM-1800.2-2020-2.0.tar.gz

# 환경 변수 설정 (~/.bashrc에 추가)
export UVM_HOME=/path/to/uvm-1800.2
```

**시뮬레이터별 UVM 컴파일 옵션**:

| 시뮬레이터 | 컴파일 명령 | UVM 옵션 |
|-----------|------------|---------|
| **VCS** | `vcs` | `-sverilog -ntb_opts uvm-1.2` (또는 `-ntb_opts uvm`) |
| **Questa** | `vlog + vsim` | `+incdir+$UVM_HOME/src $UVM_HOME/src/uvm_pkg.sv` |
| **Xcelium** | `xrun` | `-uvm -uvmhome $UVM_HOME` |

> **중요**: 시뮬레이터마다 옵션이 다릅니다. 이 표를 북마크해두고 필요할 때 참조하세요. 최신 버전의 시뮬레이터에서는 UVM이 내장되어 있어 별도 옵션 없이 사용할 수 있는 경우도 있습니다.

### 2.5.5 첫 로컬 컴파일 테스트

위 Hello World 코드([예제 2-1])를 `testbench.sv` 파일로 저장하고:

```bash
# Questa로 컴파일 및 실행
vlib work
vlog +incdir+$UVM_HOME/src $UVM_HOME/src/uvm_pkg.sv testbench.sv
vsim -c work.top -do "run -all; quit"

# VCS로 컴파일 및 실행
vcs -sverilog -ntb_opts uvm-1.2 testbench.sv -o simv
./simv

# Xcelium으로 컴파일 및 실행
xrun -uvm testbench.sv
```

> **참고**: 코드에서 `run_test("hello_test")`로 테스트 이름을 직접 지정했으므로, 커맨드라인에서 `+UVM_TESTNAME`은 생략할 수 있습니다. 실무에서는 `run_test()`를 인자 없이 호출하고, 커맨드라인에서 `+UVM_TESTNAME=테스트명`으로 테스트를 지정하는 패턴을 더 많이 사용합니다. 이렇게 하면 코드를 수정하지 않고도 다양한 테스트를 실행할 수 있기 때문입니다.

EDA Playground에서 본 것과 동일한 출력이 나오면 로컬 환경 설정 성공입니다.

---

## 2.6 UVM 프로젝트 디렉토리 구조

### 2.6.1 실무 표준 디렉토리 구조

> **이 구조를 지금 만들 필요도, 외울 필요도 없습니다.** 아래에 나오는 agents, sequences, scoreboard 같은 이름은 아직 배우지 않은 개념입니다. 각 폴더가 무슨 역할을 하는지는 해당 챕터에서 하나씩 만들면서 자연스럽게 배우게 됩니다. 지금은 "실무에서는 이런 식으로 파일을 정리한다"는 것만 훑어보세요.

팹리스 회사에서 실제로 사용하는 UVM 프로젝트 구조입니다:

```
project_root/
├── rtl/                    # RTL 설계 파일 (검증 대상, DUT)
│   ├── uart_tx.sv
│   └── uart_rx.sv
│
├── tb/                     # 테스트벤치 (UVM 검증 환경)
│   ├── env/                # 환경 컴포넌트
│   │   └── uart_env.sv
│   ├── agents/             # 에이전트 (Driver, Monitor, Sequencer)
│   │   ├── uart_agent.sv
│   │   ├── uart_driver.sv
│   │   ├── uart_monitor.sv
│   │   └── uart_sequencer.sv
│   ├── sequences/          # 시퀀스 (테스트 데이터 생성)
│   │   └── uart_base_seq.sv
│   ├── tests/              # 테스트 케이스
│   │   ├── uart_base_test.sv
│   │   └── uart_smoke_test.sv
│   ├── scoreboard/         # 스코어보드 (결과 비교)
│   │   └── uart_scoreboard.sv
│   ├── interfaces/         # 인터페이스 (DUT 연결용)
│   │   └── uart_if.sv
│   └── top/                # 최상위 모듈
│       └── tb_top.sv
│
├── sim/                    # 시뮬레이션 실행
│   ├── Makefile            # 빌드 스크립트
│   └── run.sh              # 실행 스크립트
│
└── docs/                   # 문서
    └── testplan.md         # 테스트 계획서
```

### 2.6.2 각 디렉토리의 역할

| 디렉토리 | 역할 | 비유 | 배우는 챕터 |
|----------|------|------|-----------|
| `rtl/` | 검증 대상(DUT) 설계 파일 | 검사할 제품 | Chapter 5 |
| `tb/env/` | 검증 환경 최상위 | 검사실 전체 | Chapter 5 |
| `tb/agents/` | 에이전트 (Driver+Monitor+Sequencer) | 검사 장비 세트 | Chapter 7 |
| `tb/sequences/` | 테스트 데이터 생성기 | 검사 시나리오 | Chapter 6 |
| `tb/tests/` | 테스트 케이스 | 검사 지시서 | Chapter 9 |
| `tb/scoreboard/` | 결과 비교 판정기 | 합격/불합격 판정원 | Chapter 8 |
| `tb/interfaces/` | DUT와 테스트벤치 연결 | 검사 장비의 연결 케이블 | Chapter 7 |
| `tb/top/` | 시뮬레이션 시작점 | 검사실 출입구 | Chapter 5 |
| `sim/` | 컴파일/실행 스크립트 | 검사 절차 매뉴얼 | Chapter 5 |

### 2.6.3 간단한 Makefile 맛보기

실무에서는 명령어를 직접 타이핑하지 않고 Makefile을 사용합니다. 지금은 Makefile 문법을 몰라도 됩니다. Chapter 5에서 실제 프로젝트를 만들며 함께 작성합니다. "make run 하면 실행된다" 정도만 기억하세요:

```makefile
# 파일: sim/Makefile
# 설명: UVM 시뮬레이션 빌드 스크립트 (Questa 기준)

# 시뮬레이터 설정
SIMULATOR = questa
UVM_HOME  = /path/to/uvm-1800.2

# 소스 파일
TB_TOP    = ../tb/top/tb_top.sv
RTL_FILES = ../rtl/*.sv
TB_FILES  = ../tb/**/*.sv

# 기본 타겟: 컴파일 후 실행
all: compile run

# 컴파일
compile:
	vlib work
	vlog +incdir+$(UVM_HOME)/src \
	     $(UVM_HOME)/src/uvm_pkg.sv \
	     $(RTL_FILES) $(TB_FILES) $(TB_TOP)

# 시뮬레이션 실행
run:
	vsim -c work.tb_top \
	     +UVM_TESTNAME=$(TEST) \
	     -do "run -all; quit"

# 파형 뷰어로 실행 (GUI 모드)
gui:
	vsim work.tb_top \
	     +UVM_TESTNAME=$(TEST)

# 정리
clean:
	rm -rf work transcript *.wlf

# 사용법 표시
help:
	@echo "사용법:"
	@echo "  make compile        - 컴파일"
	@echo "  make run TEST=hello_test  - 시뮬레이션 실행"
	@echo "  make gui TEST=hello_test  - GUI 모드 실행"
	@echo "  make clean          - 정리"
```

> **주의**: Makefile의 들여쓰기는 반드시 **탭(Tab)** 문자를 사용해야 합니다. 스페이스로 들여쓰면 make 에러가 발생합니다.

**사용법**:
```bash
cd sim/
make compile                    # 컴파일
make run TEST=hello_test        # hello_test 실행
make clean                      # 정리
```

---

## 2.7 체크포인트

### 셀프 체크

아래 질문에 답할 수 있다면 이 챕터를 충분히 이해한 것입니다:

1. SystemVerilog 시뮬레이터 3가지를 나열할 수 있는가?

<details>
<summary>정답 확인</summary>
VCS (Synopsys), Questa (Siemens EDA), Xcelium (Cadence)
</details>

2. UVM 프로그램에 반드시 포함해야 하는 2줄은 무엇인가?

<details>
<summary>정답 확인</summary>

```systemverilog
`include "uvm_macros.svh"
import uvm_pkg::*;
```
</details>

3. `uvm_info`의 3개 인자는 각각 무엇인가?

<details>
<summary>정답 확인</summary>

1. 메시지 태그(TAG) - 분류용 문자열
2. 메시지 내용 - 출력할 텍스트
3. 출력 상세 수준(Verbosity) - UVM_NONE, UVM_LOW, UVM_MEDIUM, UVM_HIGH, UVM_FULL, UVM_DEBUG
</details>

4. `phase.raise_objection(this)`를 빠뜨리면 어떤 일이 벌어지는가?

<details>
<summary>정답 확인</summary>
시뮬레이션이 run_phase에 진입하자마자 바로 종료됩니다. UVM은 아무도 오브젝션(Objection)을 제기하지 않으면 "할 일이 없다"고 판단하고 즉시 다음 페이즈로 넘어갑니다. 그 결과, #delay 이후에 배치된 코드는 실행되지 않습니다.
</details>

5. `function`과 `task`의 차이는 무엇인가?

<details>
<summary>정답 확인</summary>
`function`은 시간 지연(#delay) 없이 즉시 실행됩니다. `task`는 시간 지연을 사용할 수 있어서 시뮬레이션 시간이 흐를 수 있습니다. run_phase는 시간 지연이 필요하므로 `task`로 선언합니다.
</details>

### 연습문제

**[실습 2-1] (쉬움)**: Hello World 코드에서 메시지 태그를 "HELLO" 대신 자신의 이름으로 바꿔보세요. UVM Report Summary에서 태그별 카운트가 어떻게 변하나요?

<details>
<summary>힌트</summary>

`uvm_info("MY_NAME", "메시지", UVM_LOW)` 처럼 태그 문자열을 변경하면 됩니다. Report Summary의 "Report counts by id" 섹션에서 변경된 태그 이름이 표시됩니다.
</details>

**[실습 2-2] (보통)**: `uvm_info`, `uvm_warning`, `uvm_error`를 각각 2개씩 출력하는 테스트를 작성하세요. UVM Report Summary의 결과를 확인하세요.

<details>
<summary>힌트</summary>

run_phase 안에 6개의 메시지를 배치하면 됩니다. Report Summary에서 INFO 개수가 증가하고, WARNING: 2, ERROR: 2가 표시되어야 합니다.
</details>

**[실습 2-3] (도전)**: `uvm_error`를 15개 출력하는 테스트를 작성하세요. 시뮬레이션이 끝까지 실행되나요? 왜 그런지 생각해보세요. (힌트: UVM의 기본 에러 한도는 10개입니다. 커맨드라인 옵션 `+UVM_MAX_QUIT_COUNT`로 변경할 수 있습니다.)

### 다음 챕터 미리보기

> Chapter 3에서는 UVM을 본격적으로 배우기 전에 필요한 **SystemVerilog 핵심 문법**을 다룹니다. 클래스(Class), 인터페이스(Interface), 랜덤화(Randomization) 등 UVM에서 가장 많이 쓰는 SystemVerilog 기능을 집중 학습합니다.
