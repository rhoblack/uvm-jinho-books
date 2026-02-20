# Chapter 5: 첫 UVM 테스트벤치

> **학습 목표**
> - Virtual Interface의 역할과 사용법을 이해한다
> - `uvm_config_db`로 설정값(virtual interface)을 전달할 수 있다
> - 간단한 DUT(4비트 카운터)에 대한 완전한 UVM 테스트벤치를 작성할 수 있다
> - 드라이버/모니터의 기본 동작 원리를 이해한다
> - 시뮬레이션을 실행하고 결과를 해석할 수 있다

> **선수 지식**: Chapter 3에서 배운 interface, class, extends를 사용합니다. Chapter 4에서 배운 uvm_component, Factory(type_id::create), Phase(build/connect/run)가 핵심 기반입니다.

---

## 5.1 DUT 소개 — 4비트 업카운터

> **이 절의 목표**: 검증할 대상(DUT)을 이해합니다. 이 챕터 전체에서 사용할 간단한 카운터입니다.

### 5.1.1 검증할 대상: 4비트 카운터

드디어 실제 DUT를 검증합니다! Chapter 1-4까지는 UVM의 개념과 구조를 배웠고, 이제부터는 **진짜 검증**을 시작합니다.

검증할 DUT는 4비트 업카운터입니다. 디지털 회로 수업에서 배운 바로 그 카운터입니다:

```systemverilog
// 파일: counter.sv
// DUT: 4비트 업카운터
// - rst_n = 0이면 카운트 초기화
// - enable = 1이면 클럭마다 1씩 증가
// - 15(4'hF) 다음에 0으로 돌아감 (오버플로)

module counter (
  input  logic       clk,
  input  logic       rst_n,    // Active-low 리셋
  input  logic       enable,   // 카운트 활성화
  output logic [3:0] count     // 4비트 카운트 값
);

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      count <= 4'b0;
    else if (enable)
      count <= count + 1;
  end

endmodule
```

> **왜 카운터인가?**: 카운터는 입력(clk, rst_n, enable)과 출력(count)이 명확하고, 동작도 직관적입니다. 복잡한 프로토콜 없이 UVM 테스트벤치의 **구조**에 집중할 수 있습니다.

### 5.1.2 Interface 정의

Chapter 3에서 interface를 배웠습니다. DUT와 테스트벤치를 연결하는 interface를 정의합니다:

```systemverilog
// 파일: counter_if.sv
// DUT와 테스트벤치를 연결하는 인터페이스
// 클럭, 리셋, 입력(enable), 출력(count)을 묶어서 관리

interface counter_if (input logic clk);
  logic       rst_n;
  logic       enable;
  logic [3:0] count;
endinterface
```

> **참고**: 실무에서는 interface 안에 **클럭킹 블록(clocking block)**과 **modport**를 추가하여 드라이버/모니터의 타이밍 안정성과 접근 권한을 관리합니다. 이 기능은 Chapter 7에서 자세히 다룹니다. 지금은 가장 단순한 형태로 시작합니다.

```
전체 연결 구조:

┌──────────────────────────────────────────────────────┐
│  테스트벤치 (UVM)                                     │
│                                                       │
│  ┌─────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Test    │    │   Driver     │    │   Monitor    │ │
│  │         │    │  (신호 구동)  │    │  (신호 관찰)  │ │
│  └─────────┘    └──────┬───────┘    └──────┬───────┘ │
│                        │                    │         │
├────────────────────────┼────────────────────┼─────────┤
│                   counter_if (Interface)               │
├────────────────────────┼────────────────────┼─────────┤
│                        │                    │         │
│  ┌─────────────────────┴────────────────────┘         │
│  │  DUT: counter                                      │
│  │  clk, rst_n, enable → count[3:0]                  │
│  └────────────────────────────────────────────────────┘
└──────────────────────────────────────────────────────┘
```

---

## 5.2 Virtual Interface — 왜 필요한가

> **이 절의 목표**: UVM 클래스에서 DUT 신호에 접근하기 위해 virtual interface가 왜 필요한지 이해하고, 사용법을 익힙니다.

### 5.2.1 문제: class에서 interface에 접근할 수 없다

UVM의 드라이버와 모니터는 **class**입니다. DUT의 신호는 **module/interface** 영역에 있습니다. SystemVerilog에서 class는 module의 신호를 직접 참조할 수 없습니다:

```systemverilog
// ❌ 불가능! class에서 interface 인스턴스를 직접 참조 불가
class my_driver extends uvm_driver;
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    top.vif.enable = 1;  // 컴파일 에러! class → module 접근 불가
  endfunction
endclass
```

이것은 SystemVerilog의 근본적인 규칙입니다:
- **module 영역** (정적): module, interface, wire, reg — 합성(synthesis) 대상
- **class 영역** (동적): class, object, handle — 시뮬레이션에서만 존재

이 두 세계를 연결하는 다리가 바로 **virtual interface**입니다.

### 5.2.2 해결: virtual interface

`virtual interface`는 interface에 대한 **참조(핸들)**입니다. class 안에서 module 영역의 interface를 가리키는 포인터라고 생각하면 됩니다:

```
module 영역                      class 영역 (UVM)

┌──────────────┐          ┌────────────────────┐
│  counter_if  │          │   my_driver        │
│  (실제 신호) │  ◄─────  │   virtual counter_if vif; │
│  .enable     │  참조    │   vif.enable = 1;  │
│  .count      │          │   (가능!)           │
└──────────────┘          └────────────────────┘
```

> **비유**: virtual interface = **리모컨**
> - Interface = TV (실제 장치)
> - Virtual interface = 리모컨 (TV를 제어하는 참조)
> - class 안에서 리모컨(virtual interface)으로 TV(interface)를 조작합니다
> - 리모컨이 없으면 TV를 제어할 수 없듯이, virtual interface가 없으면 DUT 신호에 접근할 수 없습니다

### 5.2.3 virtual interface 선언과 사용

```systemverilog
// class 내부에서 virtual interface 선언
class my_driver extends uvm_component;
  `uvm_component_utils(my_driver)

  virtual counter_if vif;  // ⭐ virtual 키워드가 핵심!

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual task run_phase(uvm_phase phase);
    phase.raise_objection(this);

    // virtual interface를 통해 DUT 신호 접근 가능!
    vif.rst_n  = 0;              // 리셋 활성화
    @(posedge vif.clk);          // 클럭 대기
    vif.rst_n  = 1;              // 리셋 해제
    vif.enable = 1;              // 카운터 활성화
    repeat(5) @(posedge vif.clk); // 5클럭 대기

    `uvm_info(get_type_name(),
      $sformatf("카운터 값: %0d", vif.count), UVM_MEDIUM)

    phase.drop_objection(this);
  endtask
endclass
```

> **핵심**: `virtual counter_if vif;`로 선언하면 class에서 interface의 신호에 접근할 수 있습니다. 하지만 선언만으로는 부족합니다 — vif에 실제 interface를 **연결**해야 합니다. 이것이 다음 절의 `uvm_config_db`입니다.

### 5.2.4 흔한 실수: virtual interface를 연결 안 하면?

```systemverilog
virtual counter_if vif;  // 선언만 함 (연결 안 함)

virtual task run_phase(uvm_phase phase);
  vif.drv_cb.enable <= 1;  // null 참조 에러!
endtask
```

```
에러 메시지:
** Fatal: (SIGSEGV) Bad handle or reference.
```

`vif`가 아무 interface도 가리키고 있지 않기 때문입니다. Chapter 3에서 배운 "핸들은 선언만으로는 null"과 같은 원리입니다. 다음 절에서 `uvm_config_db`로 연결하는 방법을 배웁니다.

> **면접 빈출**: "Virtual interface란 무엇이고 왜 필요한가요?"는 팹리스 면접에서 매우 자주 나옵니다. "class에서 module/interface 영역의 신호에 접근하기 위한 참조(핸들)" 이라고 답하면 됩니다.

---

## 5.3 uvm_config_db — 설정값 전달 메커니즘

> **이 절의 목표**: `uvm_config_db`의 set/get 패턴을 이해하고, virtual interface를 테스트벤치 컴포넌트에 전달할 수 있습니다.

### 5.3.1 config_db가 필요한 이유

virtual interface를 연결하는 방법이 필요합니다. 다음과 같은 상황을 생각해봅시다:

```
문제: top 모듈에서 만든 interface를 어떻게 UVM 클래스로 전달하지?

module top;
  counter_if vif(clk);     // interface는 module 영역에서 생성
  counter dut(             // DUT 연결
    .clk(clk), .rst_n(vif.rst_n), .enable(vif.enable), .count(vif.count)
  );
  initial run_test("my_test");  // UVM 테스트 시작
endmodule

// my_driver는 class — vif를 어떻게 받지?
```

직접 전달할 방법이 없습니다 — class 생성자에 interface를 파라미터로 넣을 수도 없고, 전역 변수를 쓰는 것은 나쁜 설계입니다.

`uvm_config_db`는 이 문제를 해결하는 **글로벌 설정 저장소**입니다:

```
┌──────────────────────────────────────────────┐
│           uvm_config_db (글로벌 저장소)        │
│                                               │
│  ┌─────┐     set()      ┌─────────┐          │
│  │ top │  ───────────→  │  "vif"  │          │
│  │모듈 │   interface    │  = vif  │          │
│  └─────┘     저장       └────┬────┘          │
│                              │               │
│  ┌──────────┐   get()   ┌───┘               │
│  │ driver   │ ◄────────                     │
│  │ (class)  │  interface                     │
│  └──────────┘   가져오기                     │
└──────────────────────────────────────────────┘
```

> **비유**: config_db = **호텔 프런트 데스크**
> - `set()` = 프런트에 열쇠를 맡김 ("305호 열쇠 맡길게요")
> - `get()` = 프런트에서 열쇠를 찾음 ("305호 열쇠 주세요")
> - 맡긴 사람과 찾는 사람이 직접 만날 필요 없음 (느슨한 결합)

### 5.3.2 config_db 사용법: set()과 get()

**1단계: set() — 값 저장 (보통 top 모듈에서)**

```systemverilog
// top 모듈에서 interface를 config_db에 저장
module top;
  logic clk;
  counter_if vif(clk);  // interface 생성
  counter dut(
    .clk(clk), .rst_n(vif.rst_n),
    .enable(vif.enable), .count(vif.count)
  );

  initial begin
    // ⭐ config_db에 virtual interface 저장
    uvm_config_db#(virtual counter_if)::set(
      null,       // 컨텍스트 (null = 전역)
      "*",        // 대상 경로 (* = 모든 컴포넌트)
      "vif",      // 이름 (get할 때 이 이름으로 찾음)
      vif         // 저장할 값 (actual interface)
    );
    run_test("counter_test");
  end

  // 클럭 생성
  initial begin
    clk = 0;
    forever #5 clk = ~clk;  // 10ns 주기
  end
endmodule
```

> **실무 참고**: 위 예제에서 `set(null, "*", ...)` 패턴은 모든 컴포넌트가 접근할 수 있도록 전역 설정입니다. 학습용으로는 충분하지만, 실무에서는 `set(this, "env.agent.drv", "vif", vif)` 처럼 특정 컴포넌트 경로를 지정하여 범위를 좁히는 것이 좋습니다. 지금은 `"*"` 패턴만 사용합니다.

**2단계: get() — 값 가져오기 (보통 build_phase에서)**

```systemverilog
// 드라이버에서 config_db로부터 virtual interface 가져오기
class counter_driver extends uvm_component;
  `uvm_component_utils(counter_driver)

  virtual counter_if vif;  // virtual interface 핸들

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    // ⭐ config_db에서 virtual interface 가져오기
    if (!uvm_config_db#(virtual counter_if)::get(
          this,     // 현재 컴포넌트
          "",       // 상대 경로 (비어있으면 현재 위치)
          "vif",    // 이름 (set할 때 사용한 이름과 동일!)
          vif       // 가져온 값을 저장할 변수
        ))
      `uvm_fatal(get_type_name(), "config_db에서 vif를 찾지 못했습니다!")
  endfunction
endclass
```

### 5.3.3 set/get 패턴 정리

```systemverilog
// set() 패턴: 값 저장
uvm_config_db#(타입)::set(컨텍스트, 경로, 이름, 값);

// get() 패턴: 값 가져오기
uvm_config_db#(타입)::get(컨텍스트, 경로, 이름, 변수);
```

| 파라미터 | set()에서 | get()에서 |
|----------|----------|----------|
| 타입 | `virtual counter_if` | `virtual counter_if` (동일해야 함) |
| 컨텍스트 | `null` (전역) | `this` (현재 컴포넌트) |
| 경로 | `"*"` (모든 대상) | `""` (현재 위치) |
| 이름 | `"vif"` (저장 이름) | `"vif"` (동일해야 함!) |
| 값/변수 | `vif` (저장할 값) | `vif` (가져올 변수) |

> **기억하세요**: set()과 get()에서 **타입**과 **이름**이 반드시 같아야 합니다. 하나라도 다르면 get()이 실패합니다.

> **안심하세요**: config_db의 문법이 길고 복잡해 보이지만, 실제로 사용하는 패턴은 **set/get 딱 2가지**뿐입니다. 위의 코드를 그대로 복사해서 타입과 이름만 바꾸면 됩니다. UVM 코드를 많이 작성하다 보면 자연스럽게 외워집니다.

### 5.3.4 흔한 실수: config_db get 실패

```systemverilog
// ❌ 실수 1: 이름이 다름
uvm_config_db#(virtual counter_if)::set(null, "*", "vif", vif);      // set: "vif"
uvm_config_db#(virtual counter_if)::get(this, "", "counter_vif", vif); // get: "counter_vif" ← 다르다!

// ❌ 실수 2: 타입이 다름
uvm_config_db#(virtual counter_if)::set(null, "*", "vif", vif);       // set: counter_if
uvm_config_db#(virtual other_if)::get(this, "", "vif", other_vif);     // get: other_if ← 다르다!

// ❌ 실수 3: set()을 빠뜨림
// top 모듈에서 set()을 호출하지 않으면 get()이 실패합니다
```

```
에러 메시지:
UVM_FATAL @ 0: uvm_test_top.env.agent.drv [counter_driver] config_db에서 vif를 찾지 못했습니다!
```

> **디버깅 팁**: config_db get이 실패하면 먼저 3가지를 확인하세요:
> 1. top 모듈에서 `set()`을 호출했는가?
> 2. set()과 get()의 **이름**("vif")이 같은가?
> 3. set()과 get()의 **타입**(virtual counter_if)이 같은가?

### 5.3.5 실습: config_db로 virtual interface 전달

**[예제 5-1] Virtual Interface 전달 테스트**

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 5-1] config_db로 virtual interface 전달
// 목적: set/get으로 virtual interface를 전달하고 DUT 신호에 접근
// 시뮬레이터 설정: SystemVerilog, UVM 1.2

`include "uvm_macros.svh"
import uvm_pkg::*;

// ── DUT ──
module counter (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       enable,
  output logic [3:0] count
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) count <= 4'b0;
    else if (enable) count <= count + 1;
  end
endmodule

// ── Interface ──
interface counter_if (input logic clk);
  logic       rst_n;
  logic       enable;
  logic [3:0] count;
endinterface

// ── 간단한 드라이버 ──
class simple_driver extends uvm_component;
  `uvm_component_utils(simple_driver)

  virtual counter_if vif;  // virtual interface 핸들

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    // config_db에서 virtual interface 가져오기
    if (!uvm_config_db#(virtual counter_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "config_db에서 vif를 찾을 수 없습니다!")
    `uvm_info(get_type_name(), "virtual interface 연결 성공!", UVM_MEDIUM)
  endfunction

  virtual task run_phase(uvm_phase phase);
    phase.raise_objection(this);

    // 리셋
    vif.rst_n  = 0;
    vif.enable = 0;
    @(posedge vif.clk);
    @(posedge vif.clk);
    vif.rst_n  = 1;
    `uvm_info(get_type_name(), "리셋 해제", UVM_MEDIUM)

    // 카운터 활성화
    vif.enable = 1;
    repeat(5) begin
      @(posedge vif.clk);
      `uvm_info(get_type_name(),
        $sformatf("카운터 값: %0d", vif.count), UVM_MEDIUM)
    end

    vif.enable = 0;
    phase.drop_objection(this);
  endtask
endclass

// ── 테스트 ──
class config_test extends uvm_test;
  `uvm_component_utils(config_test)

  simple_driver drv;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    drv = simple_driver::type_id::create("drv", this);
  endfunction
endclass

// ── Top 모듈 ──
module top;
  logic clk;

  // 클럭 생성
  initial begin
    clk = 0;
    forever #5 clk = ~clk;
  end

  // Interface 인스턴스
  counter_if vif(clk);

  // DUT 연결
  counter dut (
    .clk    (clk),
    .rst_n  (vif.rst_n),
    .enable (vif.enable),
    .count  (vif.count)
  );

  initial begin
    // ⭐ config_db에 virtual interface 저장
    uvm_config_db#(virtual counter_if)::set(null, "*", "vif", vif);
    run_test("config_test");
  end
endmodule
```

**예상 출력**:
```
UVM_INFO @ 0: uvm_test_top.drv [simple_driver] virtual interface 연결 성공!
UVM_INFO @ 0: uvm_test_top.drv [simple_driver] 리셋 해제
UVM_INFO @ 15: uvm_test_top.drv [simple_driver] 카운터 값: 1
UVM_INFO @ 25: uvm_test_top.drv [simple_driver] 카운터 값: 2
UVM_INFO @ 35: uvm_test_top.drv [simple_driver] 카운터 값: 3
UVM_INFO @ 45: uvm_test_top.drv [simple_driver] 카운터 값: 4
UVM_INFO @ 55: uvm_test_top.drv [simple_driver] 카운터 값: 5
```

> **성취감 포인트**: 축하합니다! UVM 클래스에서 DUT의 실제 신호를 읽고 제어할 수 있게 되었습니다. virtual interface + config_db 조합이 바로 UVM에서 DUT를 연결하는 표준 방법입니다.

> **참고**: 예상 출력의 타임스탬프는 시뮬레이터와 클럭 설정에 따라 다를 수 있습니다. 카운터 값이 1, 2, 3, 4, 5로 증가하면 정상입니다.

---

## 5.4 드라이버와 모니터 기초

> **이 절의 목표**: 드라이버(신호 구동)와 모니터(신호 관찰)의 역할을 이해하고, virtual interface를 사용하여 기본 동작을 구현합니다.

### 5.4.1 드라이버 = 신호를 보내는 역할

드라이버는 테스트 시나리오에 따라 DUT의 입력 신호를 **구동(drive)**합니다:

```systemverilog
class counter_driver extends uvm_component;
  `uvm_component_utils(counter_driver)

  virtual counter_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual counter_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "vif를 찾을 수 없습니다!")
  endfunction

  // 리셋 태스크
  virtual task reset_dut();
    vif.rst_n  = 0;
    vif.enable = 0;
    repeat(2) @(posedge vif.clk);
    vif.rst_n  = 1;
    @(posedge vif.clk);
    `uvm_info(get_type_name(), "DUT 리셋 완료", UVM_MEDIUM)
  endtask

  // 카운트 활성화 태스크
  virtual task drive_count(int num_clocks);
    vif.enable = 1;
    repeat(num_clocks) @(posedge vif.clk);
    vif.enable = 0;
    `uvm_info(get_type_name(),
      $sformatf("%0d 클럭 동안 카운트 완료", num_clocks), UVM_MEDIUM)
  endtask

  virtual task run_phase(uvm_phase phase);
    phase.raise_objection(this);

    reset_dut();
    drive_count(10);  // 10클럭 동안 카운트

    #20;  // 안정화 대기
    phase.drop_objection(this);
  endtask
endclass
```

> **실무 참고**: 실제 프로젝트에서 드라이버는 Sequencer로부터 트랜잭션을 받아서 신호로 변환합니다 (Chapter 6-7에서 배움). 지금은 run_phase에서 직접 구동하는 단순한 형태입니다.

### 5.4.2 모니터 = 신호를 관찰하는 역할

모니터는 DUT의 출력 신호를 **관찰(monitor)**하고 기록합니다. 모니터는 신호를 바꾸지 않고 읽기만 합니다:

```systemverilog
class counter_monitor extends uvm_component;
  `uvm_component_utils(counter_monitor)

  virtual counter_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual counter_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "vif를 찾을 수 없습니다!")
  endfunction

  virtual task run_phase(uvm_phase phase);
    // 모니터는 objection을 raise하지 않음 (관찰자이므로)
    forever begin
      @(posedge vif.clk);
      if (vif.rst_n && vif.enable) begin
        `uvm_info(get_type_name(),
          $sformatf("[관찰] enable=%0b, count=%0d",
                    vif.enable, vif.count), UVM_HIGH)
      end
    end
  endtask
endclass
```

> **핵심 차이**:
> | 항목 | 드라이버 | 모니터 |
> |------|---------|--------|
> | 역할 | DUT 입력 신호 구동 | DUT 신호 관찰/기록 |
> | 신호 접근 | 읽기 + 쓰기 | 읽기만 |
> | objection | raise/drop 함 | 하지 않음 (관찰자) |
> | 비유 | 실험자 (자극을 줌) | 기록원 (결과를 적음) |

### 5.4.3 에이전트 = 드라이버 + 모니터 묶음

Chapter 4에서 배운 것처럼, 에이전트는 드라이버와 모니터를 하나로 묶는 컨테이너입니다:

```systemverilog
class counter_agent extends uvm_agent;
  `uvm_component_utils(counter_agent)

  counter_driver  drv;
  counter_monitor mon;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    drv = counter_driver::type_id::create("drv", this);
    mon = counter_monitor::type_id::create("mon", this);
    `uvm_info(get_type_name(), "에이전트: 드라이버 + 모니터 생성", UVM_MEDIUM)
  endfunction
endclass
```

---

## 5.5 종합: 첫 완전한 UVM 테스트벤치

> **이 절의 목표**: 지금까지 배운 모든 것을 합쳐서 DUT를 검증하는 완전한 UVM 테스트벤치를 만듭니다. Chapter 4의 뼈대에 virtual interface와 DUT를 연결합니다.

### 5.5.1 전체 구조 한눈에 보기

Chapter 4에서 만든 뼈대에 두 가지가 추가됩니다:
1. **Virtual interface**: DUT와 UVM 클래스를 연결
2. **config_db**: virtual interface를 컴포넌트에 전달

```
완전한 UVM 테스트벤치 구조:

┌──────────────────────────────────────────────────┐
│  top 모듈                                         │
│                                                   │
│  ┌─ counter_test (uvm_test) ────────────────────┐│
│  │                                               ││
│  │  ┌─ counter_env (uvm_env) ──────────────────┐││
│  │  │                                           │││
│  │  │  ┌─ counter_agent (uvm_agent) ──────────┐│││
│  │  │  │                                       ││││
│  │  │  │  ┌──────────────┐  ┌───────────────┐ ││││
│  │  │  │  │counter_driver│  │counter_monitor│ ││││
│  │  │  │  │  vif ────────┼──┼── vif          │ ││││
│  │  │  │  └──────────────┘  └───────────────┘ ││││
│  │  │  │                                       ││││
│  │  │  └───────────────────────────────────────┘│││
│  │  └───────────────────────────────────────────┘││
│  └───────────────────────────────────────────────┘│
│                       ↑ config_db (vif)           │
│  ┌────────────────────┴───────────────────────┐  │
│  │           counter_if (Interface)            │  │
│  └────────────────────┬───────────────────────┘  │
│  ┌────────────────────┴───────────────────────┐  │
│  │           counter (DUT)                     │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### 5.5.2 단계별 빌드업

이제 전체 코드를 단계별로 조립합니다. 각 단계에서 무엇을 하는지 확인하면서 따라오세요.

**[예제 5-2] 완전한 UVM 테스트벤치**

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 5-2] 첫 완전한 UVM 테스트벤치
// 목적: DUT(4비트 카운터)를 UVM으로 검증하는 완전한 환경
// 시뮬레이터 설정: SystemVerilog, UVM 1.2

`include "uvm_macros.svh"
import uvm_pkg::*;

// ══════════════════════════════════════
// 1단계: DUT (검증 대상)
// ══════════════════════════════════════
module counter (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       enable,
  output logic [3:0] count
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) count <= 4'b0;
    else if (enable) count <= count + 1;
  end
endmodule

// ══════════════════════════════════════
// 2단계: Interface (DUT-TB 연결 통로)
// ══════════════════════════════════════
interface counter_if (input logic clk);
  logic       rst_n;
  logic       enable;
  logic [3:0] count;
endinterface

// ══════════════════════════════════════
// 3단계: 드라이버 (DUT 입력 신호 구동)
// ══════════════════════════════════════
class counter_driver extends uvm_component;
  `uvm_component_utils(counter_driver)

  virtual counter_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual counter_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "vif를 찾을 수 없습니다!")
  endfunction

  virtual task reset_dut();
    vif.rst_n  = 0;
    vif.enable = 0;
    repeat(2) @(posedge vif.clk);
    vif.rst_n  = 1;
    @(posedge vif.clk);
    `uvm_info(get_type_name(), "리셋 완료", UVM_MEDIUM)
  endtask

  virtual task drive_count(int num_clocks);
    vif.enable = 1;
    repeat(num_clocks) @(posedge vif.clk);
    vif.enable = 0;
  endtask

  virtual task run_phase(uvm_phase phase);
    phase.raise_objection(this);

    // 테스트 시나리오 1: 리셋 후 10클럭 카운트
    reset_dut();
    `uvm_info(get_type_name(), "=== 시나리오 1: 10클럭 카운트 ===", UVM_MEDIUM)
    drive_count(10);

    // 테스트 시나리오 2: 카운트 멈추고 재개
    `uvm_info(get_type_name(), "=== 시나리오 2: 정지 후 재개 ===", UVM_MEDIUM)
    repeat(3) @(posedge vif.clk);  // 3클럭 정지
    drive_count(5);                 // 5클럭 추가 카운트

    #20;
    phase.drop_objection(this);
  endtask
endclass

// ══════════════════════════════════════
// 4단계: 모니터 (DUT 출력 관찰)
// ══════════════════════════════════════
class counter_monitor extends uvm_component;
  `uvm_component_utils(counter_monitor)

  virtual counter_if vif;
  int expected_count;  // 예상 카운트 값 (간단한 자체 검증용)

  function new(string name, uvm_component parent);
    super.new(name, parent);
    expected_count = 0;
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual counter_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "vif를 찾을 수 없습니다!")
  endfunction

  virtual task run_phase(uvm_phase phase);
    // 리셋 해제 대기
    @(posedge vif.rst_n);

    forever begin
      @(posedge vif.clk);
      #1;  // 신호 안정화 대기 (Ch.7에서 clocking block으로 개선)

      if (!vif.rst_n) begin
        expected_count = 0;
      end else if (vif.enable) begin
        expected_count = (expected_count + 1) % 16;  // 4비트 오버플로

        // 간단한 자체 검증
        if (vif.count !== expected_count) begin
          `uvm_error(get_type_name(),
            $sformatf("불일치! 예상=%0d, 실제=%0d",
                      expected_count, vif.count))
        end else begin
          `uvm_info(get_type_name(),
            $sformatf("일치: count=%0d", vif.count), UVM_HIGH)
        end
      end
    end
  endtask
endclass

// ══════════════════════════════════════
// 5단계: 에이전트 (드라이버 + 모니터)
// ══════════════════════════════════════
class counter_agent extends uvm_agent;
  `uvm_component_utils(counter_agent)

  counter_driver  drv;
  counter_monitor mon;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    drv = counter_driver::type_id::create("drv", this);
    mon = counter_monitor::type_id::create("mon", this);
  endfunction
endclass

// ══════════════════════════════════════
// 6단계: 환경 (에이전트 컨테이너)
// ══════════════════════════════════════
class counter_env extends uvm_env;
  `uvm_component_utils(counter_env)

  counter_agent agent;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    agent = counter_agent::type_id::create("agent", this);
  endfunction
endclass

// ══════════════════════════════════════
// 7단계: 테스트 (최상위 — 시나리오 정의)
// ══════════════════════════════════════
class counter_test extends uvm_test;
  `uvm_component_utils(counter_test)

  counter_env env;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = counter_env::type_id::create("env", this);
    `uvm_info(get_type_name(), "=== 카운터 검증 테스트 시작 ===", UVM_MEDIUM)
  endfunction

  virtual function void report_phase(uvm_phase phase);
    uvm_report_server svr = uvm_report_server::get_server();
    if (svr.get_severity_count(UVM_ERROR) == 0)
      `uvm_info(get_type_name(), "=== 테스트 통과! (PASS) ===", UVM_NONE)
    else
      `uvm_error(get_type_name(), "=== 테스트 실패! (FAIL) ===")
  endfunction
endclass

// ══════════════════════════════════════
// 8단계: Top 모듈 (DUT + Interface + UVM 연결)
// ══════════════════════════════════════
module top;
  logic clk;

  // 클럭 생성: 10ns 주기 (100MHz)
  initial begin
    clk = 0;
    forever #5 clk = ~clk;
  end

  // Interface 인스턴스
  counter_if vif(clk);

  // DUT 연결
  counter dut (
    .clk    (clk),
    .rst_n  (vif.rst_n),
    .enable (vif.enable),
    .count  (vif.count)
  );

  initial begin
    // config_db에 virtual interface 저장
    uvm_config_db#(virtual counter_if)::set(null, "*", "vif", vif);
    run_test("counter_test");
  end
endmodule
```

**예상 출력**:
```
UVM_INFO @ 0: uvm_test_top [counter_test] === 카운터 검증 테스트 시작 ===
UVM_INFO @ 25: uvm_test_top.env.agent.drv [counter_driver] 리셋 완료
UVM_INFO @ 25: uvm_test_top.env.agent.drv [counter_driver] === 시나리오 1: 10클럭 카운트 ===
UVM_INFO @ 125: uvm_test_top.env.agent.drv [counter_driver] === 시나리오 2: 정지 후 재개 ===
UVM_INFO @ 0: uvm_test_top [counter_test] === 테스트 통과! (PASS) ===
```

> **관찰 포인트**:
> 1. 컴포넌트 경로: `uvm_test_top.env.agent.drv` — Chapter 4에서 배운 트리 구조!
> 2. 모니터가 에러를 보고하지 않았으므로 "테스트 통과" 출력
> 3. 시나리오 1(10클럭)과 시나리오 2(정지+재개)가 순서대로 실행됨

### 5.5.3 코드 구조 정리

전체 코드의 빌드업 구조를 다시 정리합니다:

```
파일: testbench.sv

1. DUT (counter)           — 검증할 대상
2. Interface (counter_if)  — DUT-TB 연결 통로
3. Driver (counter_driver) — DUT 입력 신호 구동
4. Monitor (counter_monitor) — DUT 출력 관찰+검증
5. Agent (counter_agent)   — 드라이버 + 모니터
6. Env (counter_env)       — 에이전트 컨테이너
7. Test (counter_test)     — 테스트 시나리오 정의
8. Top (module top)        — 모든 것을 연결

계층 구조:
top
 ├── vif (counter_if)
 ├── dut (counter)
 └── counter_test (UVM)
      └── env
           └── agent
                ├── drv  ──→ vif (config_db로 받음)
                └── mon  ──→ vif (config_db로 받음)
```

> **성취감 포인트**: 지금 만든 테스트벤치는 실무에서 사용하는 UVM 테스트벤치와 **동일한 구조**입니다! 실무에서는 여기에 Sequence(Ch.6), TLM 포트(Ch.7), Scoreboard(Ch.8)가 추가되지만, 뼈대는 지금과 같습니다.

> **면접 빈출**: "UVM 테스트벤치의 전체 구조를 설명하세요"라는 질문에 "test → env → agent → driver/monitor 계층 구조이며, virtual interface를 config_db로 전달하여 DUT와 연결한다"고 답하면 됩니다.

---

## 5.6 체크포인트

### 셀프 체크

아래 질문에 답할 수 있다면 이 챕터를 충분히 이해한 것입니다:

1. Virtual interface가 필요한 이유는?

<details>
<summary>정답 확인</summary>

UVM의 드라이버/모니터는 class이고, DUT의 신호는 module/interface 영역에 있습니다. SystemVerilog에서 class는 module의 신호를 직접 참조할 수 없으므로, interface에 대한 참조(핸들)인 virtual interface를 사용하여 class에서 DUT 신호에 접근합니다.
</details>

2. `uvm_config_db`의 `set()`과 `get()`에서 반드시 같아야 하는 것 2가지는?

<details>
<summary>정답 확인</summary>

(1) **타입**: `uvm_config_db#(virtual counter_if)` — set과 get의 # 안에 있는 타입이 동일해야 합니다.
(2) **이름**: set에서 `"vif"`로 저장했으면 get에서도 `"vif"`로 찾아야 합니다.
</details>

3. 드라이버와 모니터의 역할 차이는?

<details>
<summary>정답 확인</summary>

드라이버는 DUT의 입력 신호를 구동(write)하는 역할이고, 모니터는 DUT의 신호를 관찰(read only)하는 역할입니다. 드라이버는 run_phase에서 objection을 raise/drop하지만, 모니터는 관찰자이므로 objection을 raise하지 않습니다.
</details>

4. config_db의 get()이 실패하면 확인해야 할 3가지는?

<details>
<summary>정답 확인</summary>

(1) top 모듈에서 `set()`을 호출했는가?
(2) set()과 get()의 **이름**("vif")이 동일한가?
(3) set()과 get()의 **타입**(virtual counter_if)이 동일한가?
</details>

5. top 모듈에서 config_db::set()을 run_test() 이전에 호출해야 하는 이유는?

<details>
<summary>정답 확인</summary>

run_test()가 UVM 테스트를 시작하면 build_phase가 실행되고, 드라이버/모니터의 build_phase에서 config_db::get()을 호출합니다. set()이 run_test() 이후에 호출되면 get() 시점에 아직 값이 저장되지 않아서 실패합니다.
</details>

6. UVM 테스트벤치의 계층 구조를 위에서 아래 순서로 나열하면?

<details>
<summary>정답 확인</summary>

test → env → agent → driver / monitor
- test: 테스트 시나리오 정의, 환경 생성
- env: 에이전트(들)를 담는 컨테이너
- agent: 드라이버 + 모니터를 묶는 단위
- driver: DUT 입력 신호 구동
- monitor: DUT 신호 관찰
</details>

### 연습문제

**[실습 5-1] 리셋 검증 추가 (쉬움)** — 약 10분

[예제 5-2]의 counter_driver에 리셋 중 카운트가 0인지 확인하는 시나리오를 추가하세요. 리셋 활성화 후 count가 0인지 모니터에서 검증합니다.

<details>
<summary>힌트</summary>

드라이버의 run_phase에서 `reset_dut()` 호출 직후, `vif.count`가 0인지 확인하는 `uvm_info` 또는 assertion을 추가하세요.
</details>

<details>
<summary>모범 답안</summary>

```systemverilog
// counter_driver의 run_phase에 추가:
virtual task run_phase(uvm_phase phase);
  phase.raise_objection(this);

  // 시나리오 0: 리셋 검증
  `uvm_info(get_type_name(), "=== 시나리오 0: 리셋 검증 ===", UVM_MEDIUM)
  reset_dut();
  @(posedge vif.clk);
  #1;
  if (vif.count !== 4'b0)
    `uvm_error(get_type_name(),
      $sformatf("리셋 실패! count=%0d (예상: 0)", vif.count))
  else
    `uvm_info(get_type_name(), "리셋 검증 통과: count=0", UVM_MEDIUM)

  // 기존 시나리오 계속...
  drive_count(10);
  // ...

  phase.drop_objection(this);
endtask
```
</details>

**[실습 5-2] 오버플로 검증 (보통)** — 약 15분

4비트 카운터는 15(4'hF) 이후 0으로 돌아와야 합니다. 드라이버에서 20클럭 동안 카운트한 후, 모니터에서 오버플로(15→0 전환)가 정상적으로 발생하는지 검증하세요.

<details>
<summary>힌트</summary>

모니터의 run_phase에서 `expected_count`가 이미 모듈로 16 연산을 하고 있으므로, 드라이버에서 `drive_count(20)`을 호출하면 자연스럽게 오버플로 검증이 됩니다. 추가로, 오버플로 시점을 명시적으로 로그에 남겨보세요.
</details>

<details>
<summary>모범 답안</summary>

```systemverilog
// counter_monitor의 run_phase를 수정하여 오버플로 감지:
virtual task run_phase(uvm_phase phase);
  @(posedge vif.rst_n);
  forever begin
    @(posedge vif.clk);
    #1;
    if (!vif.rst_n) begin
      expected_count = 0;
    end else if (vif.enable) begin
      int prev_count = expected_count;
      expected_count = (expected_count + 1) % 16;

      // 오버플로 감지
      if (prev_count == 15 && expected_count == 0)
        `uvm_info(get_type_name(),
          "오버플로 감지! 15 → 0 전환 정상", UVM_MEDIUM)

      if (vif.count !== expected_count)
        `uvm_error(get_type_name(),
          $sformatf("불일치! 예상=%0d, 실제=%0d",
                    expected_count, vif.count))
    end
  end
endtask

// counter_driver의 run_phase에 추가:
// 시나리오 3: 오버플로 검증
`uvm_info(get_type_name(), "=== 시나리오 3: 오버플로 검증 ===", UVM_MEDIUM)
reset_dut();
drive_count(20);  // 20클럭: 0→1→...→15→0→1→2→3
```
</details>

**[실습 5-3] 환경에 두 번째 에이전트 추가 (도전)** — 약 20분

`counter_env`에 두 번째 에이전트(`counter_agent agent2`)를 추가하세요. 두 에이전트 모두 동일한 virtual interface를 공유하고, 각각 다른 테스트 시나리오를 실행합니다. 컴포넌트 트리(`print_topology()`)에서 agent2가 보이는지 확인하세요.

<details>
<summary>힌트</summary>

`counter_env`의 build_phase에서 `agent2 = counter_agent::type_id::create("agent2", this);`를 추가합니다. 두 에이전트의 드라이버가 동시에 같은 신호를 구동하면 충돌하므로, agent2의 드라이버는 신호를 구동하지 않고 모니터만 동작하도록 합니다.
</details>

<details>
<summary>모범 답안</summary>

```systemverilog
class counter_env extends uvm_env;
  `uvm_component_utils(counter_env)

  counter_agent agent;
  counter_agent agent2;  // 추가!

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    agent  = counter_agent::type_id::create("agent", this);
    agent2 = counter_agent::type_id::create("agent2", this);
  endfunction
endclass

// 주의: agent2의 드라이버가 신호를 구동하면 agent1과 충돌합니다.
// 실무에서는 agent의 is_active 플래그를 사용하여 드라이버를
// 비활성화합니다 (Chapter 7에서 배울 예정).
```
</details>

### 흔한 에러와 해결법

| 에러 메시지 | 원인 | 해결 |
|------------|------|------|
| `UVM_FATAL ... vif를 찾을 수 없습니다` | config_db set() 누락 또는 이름 불일치 | top 모듈의 set()과 get()의 이름/타입 확인 |
| `Bad handle or reference (SIGSEGV)` | virtual interface가 null (연결 안 됨) | build_phase에서 config_db get() 확인 |
| 카운터 값이 증가하지 않음 | enable 신호를 구동하지 않음 | 드라이버에서 `vif.enable = 1` 확인 |
| 모니터에서 불일치 에러 | 리셋 타이밍 문제 또는 `#1` 안정화 대기 누락 | 모니터에서 `#1` 추가, 리셋 후 대기 확인 |
| config_db set() 후에도 get() 실패 | set()이 run_test() 이후에 호출됨 | set()을 run_test() 이전에 호출 |

### 용어 정리

| 한글 용어 | 영어 | 설명 |
|-----------|------|------|
| 가상 인터페이스 | Virtual Interface | class에서 module의 interface에 접근하기 위한 참조(핸들) |
| 설정 데이터베이스 | config_db | UVM 컴포넌트 간 설정값을 전달하는 글로벌 저장소 |
| 드라이버 | Driver | DUT의 입력 신호를 구동하는 컴포넌트 |
| 모니터 | Monitor | DUT의 신호를 관찰하고 기록하는 컴포넌트 |
| 에이전트 | Agent | 드라이버 + 모니터를 묶는 컨테이너 컴포넌트 |
| 환경 | Environment (Env) | 에이전트(들)를 담는 최상위 검증 환경 |
| 클럭킹 블록 | Clocking Block | 타이밍 안정성을 위한 SystemVerilog 구문 |

### 다음 챕터 미리보기

> Chapter 6에서는 다음 내용을 학습합니다:
> - `uvm_sequence`와 `uvm_sequencer`로 테스트 시나리오를 체계적으로 생성
> - `uvm_sequence_item`(트랜잭션)을 정의하고 시퀀스에서 사용
> - 드라이버가 시퀀서로부터 트랜잭션을 받아 처리하는 메커니즘
> - run_phase의 하드코딩된 구동을 시퀀스 기반으로 리팩토링
>
> 이 챕터에서 만든 counter 테스트벤치가 Chapter 6의 기반입니다!
