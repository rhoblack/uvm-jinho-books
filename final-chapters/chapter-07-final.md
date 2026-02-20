# Chapter 7: 드라이버 & 모니터 심화

> **학습 목표**
> - TLM 포트(`seq_item_port`, `analysis_port`)의 역할과 연결 방법을 이해한다
> - Clocking block과 modport로 타이밍 안정성을 확보할 수 있다
> - 실무 수준의 드라이버를 작성할 수 있다
> - 모니터에서 analysis port로 트랜잭션을 브로드캐스트할 수 있다
> - Agent의 `is_active` 플래그로 능동/수동 에이전트를 구성할 수 있다

> **선수 지식**: Chapter 5의 virtual interface, driver/monitor 기초, Chapter 6의 sequence/sequencer, `get_next_item()`/`item_done()` 패턴이 핵심 기반입니다.

---

## 7.1 TLM 포트 이해

> **이 절의 목표**: Chapter 6에서 "마법처럼" 연결한 `seq_item_port`와 `seq_item_export`의 내부 동작을 이해하고, analysis port의 개념을 배웁니다.

### 7.1.1 TLM이란?

Chapter 6에서 이 코드를 기억하시나요?

```systemverilog
// agent의 connect_phase (Chapter 6)
drv.seq_item_port.connect(sqr.seq_item_export);
```

이 한 줄로 시퀀서와 드라이버가 연결되었습니다. 이 연결을 가능하게 하는 것이 **TLM(Transaction Level Modeling)** 포트입니다.

TLM은 **컴포넌트 간에 트랜잭션 객체를 주고받는 표준 인터페이스**입니다. 직접 함수를 호출하는 대신, 포트를 통해 간접적으로 통신합니다.

> **비유**: TLM 포트 = **우체통 시스템**
> - **Port** (포트) = 우편함 투입구 — 데이터를 **보내는** 쪽
> - **Export** (익스포트) = 우편함 — 데이터를 **받는** 쪽
> - **`connect()`** = 투입구와 우편함을 연결
> - 보내는 쪽은 받는 쪽이 누구인지 몰라도 됩니다 — **느슨한 결합(loose coupling)**

### 7.1.2 Sequencer-Driver TLM 연결

`uvm_driver` 기본 클래스에는 `seq_item_port`가 이미 선언되어 있고, `uvm_sequencer`에는 `seq_item_export`가 있습니다:

```systemverilog
// uvm_driver 내부 (이미 선언됨 — 사용자가 만들 필요 없음)
class uvm_driver #(type REQ=uvm_sequence_item) extends uvm_component;
  uvm_seq_item_pull_port #(REQ) seq_item_port;  // ← 이미 있음!
  ...
endclass

// uvm_sequencer 내부 (이미 선언됨)
class uvm_sequencer #(type REQ=uvm_sequence_item) extends uvm_component;
  uvm_seq_item_pull_imp #(REQ, ...) seq_item_export;  // ← 이미 있음!
  ...
endclass
```

```
Sequencer-Driver TLM 연결:

  ┌────────────────┐         ┌────────────────┐
  │   Sequencer    │         │    Driver       │
  │                │         │                 │
  │  seq_item_     │◀────────│  seq_item_      │
  │  export        │ connect │  port           │
  │                │         │                 │
  │  (데이터 제공) │         │  (데이터 요청)  │
  └────────────────┘         └────────────────┘

  drv.seq_item_port.connect(sqr.seq_item_export)
```

**핵심 포인트**: 포트와 익스포트는 UVM 기본 클래스에 이미 선언되어 있으므로, 사용자는 `connect_phase`에서 **연결만** 하면 됩니다. 만들 필요 없이 연결만!

### 7.1.3 Analysis Port — 1:N 브로드캐스트

시퀀서→드라이버 연결은 **1:1** 통신입니다. 하지만 모니터는 관찰한 데이터를 **여러 곳**에 동시에 보내야 합니다:

- 스코어보드에게 → 결과 검증용
- 커버리지 수집기에게 → 기능 커버리지 측정용
- 로거에게 → 디버깅용

이런 **1:N 브로드캐스트**를 위해 `uvm_analysis_port`를 사용합니다:

```
Analysis Port — 1:N 브로드캐스트:

                         ┌─────────────────┐
                    ┌───▶│  Scoreboard     │
                    │    │  (검증)          │
  ┌──────────┐     │    └─────────────────┘
  │ Monitor  │     │
  │          │─────┤    ┌─────────────────┐
  │ analysis │     ├───▶│  Coverage       │
  │ _port    │     │    │  (커버리지)      │
  └──────────┘     │    └─────────────────┘
                   │
                   │    ┌─────────────────┐
                   └───▶│  Logger         │
                        │  (로깅)          │
                        └─────────────────┘
```

| 비교 | seq_item_port (1:1) | analysis_port (1:N) |
|------|--------------------|--------------------|
| 방향 | 드라이버가 시퀀서에게 **요청** | 모니터가 구독자에게 **전송** |
| 연결 수 | 1개만 | 여러 개 가능 |
| 메서드 | `get_next_item()` / `item_done()` | `write()` |
| 용도 | 시퀀스 실행 | 관찰 데이터 브로드캐스트 |

### 7.1.4 Analysis Port 사용법

**보내는 쪽 (모니터)**:

```systemverilog
class counter_monitor extends uvm_monitor;
  // ⭐ analysis port 선언
  uvm_analysis_port #(counter_seq_item) ap;

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    ap = new("ap", this);  // ⭐ 포트 생성
  endfunction

  virtual task run_phase(uvm_phase phase);
    forever begin
      counter_seq_item item = counter_seq_item::type_id::create("item");
      // ... 신호 관찰 후 item에 기록 ...
      ap.write(item);  // ⭐ 브로드캐스트!
    end
  endtask
endclass
```

**받는 쪽 (스코어보드)** — Chapter 8에서 자세히 다루지만 구조를 미리 봅니다:

```systemverilog
class counter_scoreboard extends uvm_scoreboard;
  // ⭐ analysis implementation 선언
  uvm_analysis_imp #(counter_seq_item, counter_scoreboard) ap_imp;

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    ap_imp = new("ap_imp", this);
  endfunction

  // ⭐ write() 메서드 구현 — 모니터가 write() 호출하면 자동 실행
  virtual function void write(counter_seq_item item);
    `uvm_info(get_type_name(),
      $sformatf("Received: %s", item.convert2string()), UVM_HIGH)
    // 검증 로직 (Ch.8에서 구현)
  endfunction
endclass
```

**연결 (env의 connect_phase)**:

```systemverilog
// env의 connect_phase
virtual function void connect_phase(uvm_phase phase);
  super.connect_phase(phase);
  agent.mon.ap.connect(scoreboard.ap_imp);  // 모니터 → 스코어보드
endfunction
```

> **흐름 정리**: 모니터가 `ap.write(item)`을 호출하면 → 연결된 모든 `uvm_analysis_imp`의 `write()` 메서드가 **자동으로** 호출됩니다. 사용자는 받는 쪽 클래스에 `write()` 함수를 구현하기만 하면 됩니다. UVM은 이 패턴을 더 간단하게 만든 `uvm_subscriber` 클래스도 제공합니다 — `analysis_export`가 내장되어 있어 `write()`만 구현하면 됩니다.

> **면접 포인트**: "analysis port와 일반 TLM port의 차이는?" — analysis port는 **비블로킹(non-blocking)** `write()` 메서드로 1:N 브로드캐스트하며, 연결이 없어도 에러가 아닙니다(0:N). 일반 TLM port는 1:1 연결이 필수입니다.

---

## 7.2 Clocking Block & Modport

> **이 절의 목표**: Chapter 5에서 사용한 `#1` 타이밍 해킹을 clocking block으로 개선하고, modport로 접근 권한을 제어합니다.

### 7.2.1 `#1` 해킹의 문제

Chapter 5/6에서 모니터는 이렇게 작성했습니다:

```systemverilog
// Chapter 5/6 방식: #1 해킹
virtual task run_phase(uvm_phase phase);
  forever begin
    @(posedge vif.clk);
    #1;  // ← 이것! 왜 1ns를 기다릴까?
    // 신호 샘플링...
  end
endtask
```

`#1`은 클럭 에지 직후 **1 타임 단위**를 기다려서 신호가 안정화된 후 샘플링합니다. 동작은 하지만 문제가 있습니다:

| 문제 | 설명 |
|------|------|
| 타임스케일 의존 | `1ns`인지 `1ps`인지에 따라 동작이 달라질 수 있음 |
| 표준이 아님 | IEEE 1800에 정의된 방법이 아님 |
| 경쟁 조건(race) | 복잡한 설계에서 `#1`이 충분하지 않을 수 있음 |
| 코드 리뷰 | 실무에서 `#1` 사용은 지적 사항 |

### 7.2.2 해결: Clocking Block

**Clocking block**은 신호의 샘플링/구동 타이밍을 **클럭 기준으로 명시적으로 정의**하는 SystemVerilog 구문입니다:

```systemverilog
// 개선된 interface — clocking block과 modport 추가
interface counter_if(input logic clk);
  logic       rst_n;
  logic       enable;
  logic [3:0] count;

  // ⭐ 드라이버용 clocking block
  clocking drv_cb @(posedge clk);
    default input #1step output #0;   // 입력: 이전 타임슬롯, 출력: 즉시
    output rst_n;                     // 드라이버가 구동하는 신호
    output enable;
  endclocking

  // ⭐ 모니터용 clocking block
  clocking mon_cb @(posedge clk);
    default input #1step;             // 모든 신호를 이전 타임슬롯에서 샘플
    input rst_n;                      // 모니터는 관찰만
    input enable;
    input count;
  endclocking

  // ⭐ modport — 접근 권한 제어
  modport drv_mp (clocking drv_cb, input clk);   // 드라이버: drv_cb만 접근
  modport mon_mp (clocking mon_cb, input clk);   // 모니터: mon_cb만 접근
endinterface
```

**핵심 키워드 설명**:

| 키워드 | 의미 |
|--------|------|
| `clocking drv_cb @(posedge clk)` | 클럭 양의 에지 기준 타이밍 블록 |
| `default input #1step` | 입력 신호를 **이전 타임 슬롯**(preponed region)에서 샘플 |
| `default output #0` | 출력 신호를 **현재 클럭 에지에서 즉시** 구동 (지연 없음) |
| `output rst_n` | 이 clocking block에서 `rst_n`을 출력으로 사용 |
| `input count` | 이 clocking block에서 `count`를 입력으로 사용 |

> **`#1step`이 `#1`보다 나은 이유**: `#1step`은 타임스케일에 관계없이 항상 **이전 타임 슬롯**에서 신호를 샘플합니다. IEEE 1800 표준에 정의된 방법으로, 경쟁 조건이 발생하지 않습니다.

### 7.2.3 Modport — 접근 권한 제어

Modport는 interface 신호에 대한 **방향성(direction)**을 제한합니다:

```
Modport 접근 권한:

  counter_if
  ┌───────────────────────────────────────────┐
  │  신호: rst_n, enable, count               │
  ├─────────────────────┬─────────────────────┤
  │   drv_mp            │   mon_mp            │
  │   drv_cb:           │   mon_cb:           │
  │   output rst_n  ──▶ │   input rst_n   ◀── │
  │   output enable ──▶ │   input enable  ◀── │
  │                     │   input count   ◀── │
  │   (구동만 가능)     │   (관찰만 가능)     │
  └─────────────────────┴─────────────────────┘
```

modport를 사용하면:
- 드라이버가 실수로 `count`를 구동하는 것을 **컴파일 타임에** 방지
- 모니터가 실수로 `enable`을 구동하는 것을 방지
- 코드의 의도가 명확해짐

### 7.2.4 Clocking Block 적용

이제 드라이버와 모니터에 clocking block을 적용합니다:

```systemverilog
// 드라이버 — clocking block 사용
class counter_driver extends uvm_driver #(counter_seq_item);
  `uvm_component_utils(counter_driver)

  virtual counter_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual counter_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "Virtual interface not found!")
  endfunction

  virtual task run_phase(uvm_phase phase);
    counter_seq_item item;
    // 초기화: 리셋 상태
    vif.drv_cb.rst_n  <= 0;
    vif.drv_cb.enable <= 0;

    forever begin
      seq_item_port.get_next_item(item);
      drive_item(item);
      seq_item_port.item_done();
    end
  endtask

  virtual task drive_item(counter_seq_item item);
    // ⭐ clocking block을 통해 신호 구동
    vif.drv_cb.rst_n  <= item.rst_n;
    vif.drv_cb.enable <= item.enable;
    repeat(item.cycles) @(vif.drv_cb);  // ⭐ clocking event 대기
  endtask
endclass
```

```systemverilog
// 모니터 — clocking block 사용
class counter_monitor extends uvm_monitor;
  `uvm_component_utils(counter_monitor)

  virtual counter_if vif;
  uvm_analysis_port #(counter_seq_item) ap;  // ⭐ analysis port

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual counter_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "Virtual interface not found!")
    ap = new("ap", this);  // ⭐ analysis port 생성
  endfunction

  virtual task run_phase(uvm_phase phase);
    forever begin
      counter_seq_item item;
      @(vif.mon_cb);  // ⭐ clocking event 대기 (#1 해킹 불필요!)

      item = counter_seq_item::type_id::create("item");
      // ⭐ clocking block을 통해 안정적으로 샘플링
      item.rst_n  = vif.mon_cb.rst_n;
      item.enable = vif.mon_cb.enable;
      item.count  = vif.mon_cb.count;

      ap.write(item);  // ⭐ analysis port로 브로드캐스트
      `uvm_info(get_type_name(), item.convert2string(), UVM_HIGH)
    end
  endtask
endclass
```

**Before → After 비교**:

| 항목 | Chapter 5/6 | Chapter 7 |
|------|-------------|-----------|
| 드라이버 구동 | `vif.enable <= 1` | `vif.drv_cb.enable <= 1` |
| 클럭 대기 | `@(posedge vif.clk)` | `@(vif.drv_cb)` |
| 모니터 샘플 | `#1; vif.count` | `vif.mon_cb.count` |
| 타이밍 보장 | `#1` 해킹 | IEEE 표준 `#1step` |
| 접근 제어 | 없음 | modport로 방향 제한 |

> **참고**: clocking block을 통해 출력 신호를 구동할 때는 항상 논블로킹 할당(`<=`)을 사용합니다. `vif.drv_cb.enable <= 1`처럼 쓰면 clocking block이 타이밍을 자동으로 관리합니다.

> **안심하세요**: clocking block 문법이 복잡해 보이지만, interface에 한 번 정의하면 드라이버/모니터에서는 `vif.drv_cb.신호명`, `vif.mon_cb.신호명`으로 쓰기만 하면 됩니다. 패턴은 동일합니다.

---

## 7.3 드라이버 심화

> **이 절의 목표**: 실무에서 사용하는 드라이버 패턴을 배웁니다. 프로토콜 기반 구동과 에러 핸들링을 포함합니다.

### 7.3.1 드라이버의 역할 재정의

Chapter 6에서 드라이버는 "How"만 담당한다고 했습니다. 정확히 어떤 일을 하는지 정리합니다:

1. **시퀀서에서 트랜잭션 받기** (`get_next_item()`)
2. **트랜잭션을 DUT 신호로 변환** (프로토콜 구동)
3. **완료 알림** (`item_done()`)
4. **무한 반복** (`forever`)

### 7.3.2 get_next_item vs try_next_item

두 가지 트랜잭션 요청 방법이 있습니다:

```systemverilog
// 방법 1: get_next_item() — 블로킹 (가장 일반적)
forever begin
  seq_item_port.get_next_item(item);  // 트랜잭션 올 때까지 대기
  drive_item(item);
  seq_item_port.item_done();
end

// 방법 2: try_next_item() — 논블로킹 (아이들 동작 필요 시)
forever begin
  seq_item_port.try_next_item(item);  // 즉시 반환 (null일 수 있음)
  if (item != null) begin
    drive_item(item);
    seq_item_port.item_done();
  end else begin
    drive_idle();  // 트랜잭션이 없으면 아이들 구동
  end
end
```

| 메서드 | 동작 | 사용 시점 |
|--------|------|-----------|
| `get_next_item()` | 트랜잭션이 올 때까지 **대기** | 대부분의 경우 |
| `try_next_item()` | 즉시 반환, 없으면 `null` | 아이들 상태 구동이 필요한 프로토콜 |

> **면접 포인트**: "get_next_item과 try_next_item의 차이는?" — `get_next_item()`은 블로킹으로 트랜잭션을 기다리고, `try_next_item()`은 논블로킹으로 즉시 반환합니다. 버스 프로토콜에서 아이들 사이클이 필요하면 `try_next_item()`을 사용합니다.

### 7.3.3 프로토콜 구동 패턴

실무 드라이버는 단순히 신호를 할당하는 것이 아니라, **프로토콜 타이밍**을 따릅니다. 4비트 카운터의 실무 수준 드라이버:

```systemverilog
// 실무 수준 드라이버
class counter_driver extends uvm_driver #(counter_seq_item);
  `uvm_component_utils(counter_driver)

  virtual counter_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual counter_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "Virtual interface not found!")
  endfunction

  virtual task run_phase(uvm_phase phase);
    counter_seq_item item;

    // 초기화: DUT 리셋 상태로 시작
    reset_signals();

    forever begin
      seq_item_port.get_next_item(item);
      `uvm_info(get_type_name(),
        $sformatf("Driving: %s", item.convert2string()), UVM_HIGH)
      drive_item(item);
      seq_item_port.item_done();
    end
  endtask

  // 신호 초기화
  virtual task reset_signals();
    vif.drv_cb.rst_n  <= 0;
    vif.drv_cb.enable <= 0;
    @(vif.drv_cb);  // 1 클럭 대기
  endtask

  // 트랜잭션 → 신호 변환
  virtual task drive_item(counter_seq_item item);
    vif.drv_cb.rst_n  <= item.rst_n;
    vif.drv_cb.enable <= item.enable;
    repeat(item.cycles) @(vif.drv_cb);
  endtask
endclass
```

### 7.3.4 Response 처리 (간단 소개)

드라이버가 DUT의 응답을 시퀀스에게 돌려보내야 할 때 `item_done(rsp)` 패턴을 사용합니다:

```systemverilog
// 드라이버에서 response 전달 (간단 예시)
virtual task run_phase(uvm_phase phase);
  counter_seq_item req, rsp;

  forever begin
    seq_item_port.get_next_item(req);
    drive_item(req);

    // response 생성 및 전달
    rsp = counter_seq_item::type_id::create("rsp");
    rsp.set_id_info(req);       // 요청과 응답을 매칭
    rsp.count = vif.mon_cb.count;  // DUT 출력 기록
    seq_item_port.item_done(rsp);  // ⭐ response 전달
  end
endtask
```

> **참고**: response 처리는 양방향 프로토콜(예: AXI 읽기)에서 주로 사용합니다. 카운터처럼 단순한 DUT에서는 필요하지 않은 경우가 많습니다.

---

## 7.4 모니터 심화

> **이 절의 목표**: 모니터의 핵심 역할인 트랜잭션 수집과 analysis port 브로드캐스트를 실무 수준으로 작성합니다.

### 7.4.1 모니터의 역할

모니터는 DUT 신호를 **관찰만** 하고, 절대 **구동하지 않습니다**:

1. **신호 관찰** — clocking block으로 안정적 샘플링
2. **트랜잭션 조립** — 개별 신호를 트랜잭션 객체로 변환
3. **브로드캐스트** — analysis port로 모든 구독자에게 전송

### 7.4.2 실무 수준 모니터

```systemverilog
class counter_monitor extends uvm_monitor;
  `uvm_component_utils(counter_monitor)

  virtual counter_if vif;
  uvm_analysis_port #(counter_seq_item) ap;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual counter_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "Virtual interface not found!")
    ap = new("ap", this);
  endfunction

  virtual task run_phase(uvm_phase phase);
    forever begin
      collect_transaction();
    end
  endtask

  // 트랜잭션 수집 — 핵심 로직
  virtual task collect_transaction();
    counter_seq_item item;

    @(vif.mon_cb);  // 클럭 에지 대기

    // ① 트랜잭션 생성
    item = counter_seq_item::type_id::create("item");

    // ② clocking block으로 안정적 샘플링
    item.rst_n  = vif.mon_cb.rst_n;
    item.enable = vif.mon_cb.enable;
    item.count  = vif.mon_cb.count;

    // ③ analysis port로 브로드캐스트
    ap.write(item);

    `uvm_info(get_type_name(),
      $sformatf("Observed: %s", item.convert2string()), UVM_HIGH)
  endtask
endclass
```

### 7.4.3 모니터 설계 규칙

| 규칙 | 이유 |
|------|------|
| 신호를 절대 구동하지 않는다 | 모니터는 관찰자 — DUT 동작에 영향을 주면 안 됨 |
| `is_active`에 관계없이 항상 존재 | 수동 에이전트도 모니터는 필요 |
| analysis port로만 데이터 전달 | 느슨한 결합 유지 (구독자 변경 시 모니터 수정 불필요) |
| 프로토콜 완전한 트랜잭션만 전송 | 불완전한 데이터는 검증 오류 유발 |

---

## 7.5 Agent 구성 — is_active

> **이 절의 목표**: Agent의 `is_active` 플래그로 능동(Active)/수동(Passive) 에이전트를 구성하는 방법을 배웁니다.

### 7.5.1 능동 에이전트 vs 수동 에이전트

실무에서 에이전트는 두 가지 모드로 동작합니다:

```
Agent 모드 비교:

  Active Agent (UVM_ACTIVE)         Passive Agent (UVM_PASSIVE)
  ┌────────────────────────┐       ┌────────────────────────┐
  │  counter_agent         │       │  counter_agent         │
  │                        │       │                        │
  │  ┌──────────────┐      │       │                        │
  │  │  Sequencer   │      │       │   (Sequencer 없음)     │
  │  └──────┬───────┘      │       │                        │
  │         │              │       │                        │
  │  ┌──────┴───────┐      │       │                        │
  │  │   Driver     │      │       │   (Driver 없음)        │
  │  └──────────────┘      │       │                        │
  │                        │       │                        │
  │  ┌──────────────┐      │       │  ┌──────────────┐      │
  │  │   Monitor    │      │       │  │   Monitor    │      │
  │  └──────────────┘      │       │  └──────────────┘      │
  └────────────────────────┘       └────────────────────────┘
  → DUT에 자극 인가 + 관찰        → DUT 관찰만 (자극 없음)
```

| 모드 | 구성 | 용도 |
|------|------|------|
| Active (`UVM_ACTIVE`) | Sequencer + Driver + Monitor | DUT에 자극을 인가하고 관찰 |
| Passive (`UVM_PASSIVE`) | Monitor만 | DUT 출력만 관찰 (자극 없음) |

### 7.5.2 is_active 구현

```systemverilog
class counter_agent extends uvm_agent;
  `uvm_component_utils(counter_agent)

  counter_sequencer sqr;
  counter_driver    drv;
  counter_monitor   mon;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // ⭐ 모니터는 항상 생성
    mon = counter_monitor::type_id::create("mon", this);

    // ⭐ Active일 때만 시퀀서와 드라이버 생성
    if (get_is_active() == UVM_ACTIVE) begin
      sqr = counter_sequencer::type_id::create("sqr", this);
      drv = counter_driver::type_id::create("drv", this);
    end
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);

    // ⭐ Active일 때만 연결
    if (get_is_active() == UVM_ACTIVE) begin
      drv.seq_item_port.connect(sqr.seq_item_export);
    end
  endfunction
endclass
```

**테스트에서 에이전트 모드 설정**:

```systemverilog
// 방법 1: env의 build_phase에서 직접 설정
virtual function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  agent = counter_agent::type_id::create("agent", this);
  agent.is_active = UVM_ACTIVE;   // 또는 UVM_PASSIVE
endfunction

// 방법 2: config_db로 설정
virtual function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  uvm_config_db#(uvm_active_passive_enum)::set(
    this, "env.agent", "is_active", UVM_PASSIVE);
endfunction
```

### 7.5.3 수동 에이전트 활용 예시

수동 에이전트는 DUT의 출력 인터페이스를 모니터링할 때 유용합니다:

```systemverilog
// 환경에 두 개 에이전트 구성
class counter_env extends uvm_env;
  `uvm_component_utils(counter_env)

  counter_agent input_agent;    // Active: DUT 입력 구동
  counter_agent output_agent;   // Passive: DUT 출력 관찰만

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    input_agent = counter_agent::type_id::create("input_agent", this);
    input_agent.is_active = UVM_ACTIVE;   // ⭐ 자극 인가

    output_agent = counter_agent::type_id::create("output_agent", this);
    output_agent.is_active = UVM_PASSIVE;  // ⭐ 관찰만
  endfunction
endclass
```

> **면접 포인트**: "Active Agent와 Passive Agent의 차이는?" — Active Agent는 Sequencer + Driver + Monitor로 DUT에 자극을 인가하고 관찰합니다. Passive Agent는 Monitor만 있어 DUT 신호를 관찰만 합니다. `is_active` 플래그로 build_phase에서 조건부 생성합니다.

---

## 7.6 종합: 실무 수준 테스트벤치

> **이 절의 목표**: 이 챕터에서 배운 TLM, clocking block, analysis port를 모두 적용한 완전한 테스트벤치를 작성합니다.

**[예제 7-1] 실무 수준 UVM 테스트벤치**

```systemverilog
// ================================================================
// [예제 7-1] 실무 수준 UVM 테스트벤치
// 파일: counter_adv_tb.sv
// Chapter 5/6 대비 개선: clocking block, analysis port, is_active
// ================================================================

// ---- Step 1: 개선된 Interface ----
interface counter_if(input logic clk);
  logic       rst_n;
  logic       enable;
  logic [3:0] count;

  // 드라이버용 clocking block
  clocking drv_cb @(posedge clk);
    default input #1step output #0;
    output rst_n;
    output enable;
  endclocking

  // 모니터용 clocking block
  clocking mon_cb @(posedge clk);
    default input #1step;
    input rst_n;
    input enable;
    input count;
  endclocking

  modport drv_mp (clocking drv_cb, input clk);
  modport mon_mp (clocking mon_cb, input clk);
endinterface

// ---- Step 2: DUT (변경 없음) ----
module counter (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       enable,
  output logic [3:0] count
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      count <= 4'b0;
    else if (enable)
      count <= count + 1;
  end
endmodule

// ---- Step 3: 트랜잭션 (Ch.6과 동일) ----
class counter_seq_item extends uvm_sequence_item;
  rand bit       rst_n;
  rand bit       enable;
  rand int       cycles;
  logic [3:0]    count;

  constraint c_cycles { cycles inside {[1:20]}; }

  `uvm_object_utils_begin(counter_seq_item)
    `uvm_field_int(rst_n,  UVM_ALL_ON)
    `uvm_field_int(enable, UVM_ALL_ON)
    `uvm_field_int(cycles, UVM_ALL_ON)
    `uvm_field_int(count,  UVM_ALL_ON)
  `uvm_object_utils_end

  function new(string name = "counter_seq_item");
    super.new(name);
  endfunction

  function string convert2string();
    return $sformatf("rst_n=%0b enable=%0b cycles=%0d count=%0h",
                     rst_n, enable, cycles, count);
  endfunction
endclass

// ---- Step 4: 시퀀스 (Ch.6과 동일) ----
class counter_reset_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_reset_seq)
  function new(string name = "counter_reset_seq");
    super.new(name);
  endfunction
  virtual task body();
    counter_seq_item item;
    item = counter_seq_item::type_id::create("item");
    start_item(item);
    item.rst_n = 0; item.enable = 0; item.cycles = 2;
    finish_item(item);
  endtask
endclass

class counter_count_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_count_seq)
  rand int num_transactions;
  constraint c_num { num_transactions inside {[3:10]}; }
  function new(string name = "counter_count_seq");
    super.new(name);
  endfunction
  virtual task body();
    counter_seq_item item;
    for (int i = 0; i < num_transactions; i++) begin
      item = counter_seq_item::type_id::create($sformatf("item_%0d", i));
      start_item(item);
      if (!item.randomize() with { rst_n == 1; enable == 1; cycles inside {[1:5]}; })
        `uvm_fatal(get_type_name(), "Randomization failed!")
      finish_item(item);
    end
  endtask
endclass

// ---- Step 5: 시퀀서 (Ch.6과 동일) ----
class counter_sequencer extends uvm_sequencer #(counter_seq_item);
  `uvm_component_utils(counter_sequencer)
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
endclass

// ---- Step 6: 드라이버 (⭐ clocking block 적용) ----
class counter_driver extends uvm_driver #(counter_seq_item);
  `uvm_component_utils(counter_driver)

  virtual counter_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual counter_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "Virtual interface not found!")
  endfunction

  virtual task run_phase(uvm_phase phase);
    counter_seq_item item;
    vif.drv_cb.rst_n  <= 0;
    vif.drv_cb.enable <= 0;
    forever begin
      seq_item_port.get_next_item(item);
      drive_item(item);
      seq_item_port.item_done();
    end
  endtask

  virtual task drive_item(counter_seq_item item);
    vif.drv_cb.rst_n  <= item.rst_n;
    vif.drv_cb.enable <= item.enable;
    repeat(item.cycles) @(vif.drv_cb);
  endtask
endclass

// ---- Step 7: 모니터 (⭐ clocking block + analysis port) ----
class counter_monitor extends uvm_monitor;
  `uvm_component_utils(counter_monitor)

  virtual counter_if vif;
  uvm_analysis_port #(counter_seq_item) ap;  // ⭐

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual counter_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "Virtual interface not found!")
    ap = new("ap", this);  // ⭐
  endfunction

  virtual task run_phase(uvm_phase phase);
    forever begin
      counter_seq_item item;
      @(vif.mon_cb);  // ⭐ #1 대신 clocking event
      item = counter_seq_item::type_id::create("item");
      item.rst_n  = vif.mon_cb.rst_n;
      item.enable = vif.mon_cb.enable;
      item.count  = vif.mon_cb.count;
      ap.write(item);  // ⭐ 브로드캐스트
      `uvm_info(get_type_name(), item.convert2string(), UVM_HIGH)
    end
  endtask
endclass

// ---- Step 8: 에이전트 (⭐ is_active 적용) ----
class counter_agent extends uvm_agent;
  `uvm_component_utils(counter_agent)

  counter_sequencer sqr;
  counter_driver    drv;
  counter_monitor   mon;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    mon = counter_monitor::type_id::create("mon", this);  // 항상 생성
    if (get_is_active() == UVM_ACTIVE) begin  // ⭐
      sqr = counter_sequencer::type_id::create("sqr", this);
      drv = counter_driver::type_id::create("drv", this);
    end
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    if (get_is_active() == UVM_ACTIVE) begin  // ⭐
      drv.seq_item_port.connect(sqr.seq_item_export);
    end
  endfunction
endclass

// ---- Step 9: 환경 ----
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

// ---- Step 10: 테스트 ----
class counter_test extends uvm_test;
  `uvm_component_utils(counter_test)

  counter_env env;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = counter_env::type_id::create("env", this);
  endfunction

  virtual task run_phase(uvm_phase phase);
    counter_reset_seq reset_seq;
    counter_count_seq count_seq;

    phase.raise_objection(this);

    reset_seq = counter_reset_seq::type_id::create("reset_seq");
    reset_seq.start(env.agent.sqr);

    count_seq = counter_count_seq::type_id::create("count_seq");
    count_seq.num_transactions = 5;
    count_seq.start(env.agent.sqr);

    #100;
    phase.drop_objection(this);
  endtask
endclass

// ---- Step 11: Top 모듈 ----
module top;
  logic clk;
  initial clk = 0;
  always #5 clk = ~clk;

  counter_if vif(clk);
  counter dut(
    .clk(clk), .rst_n(vif.rst_n),
    .enable(vif.enable), .count(vif.count)
  );

  initial begin
    uvm_config_db#(virtual counter_if)::set(null, "*", "vif", vif);
    run_test("counter_test");
  end

  initial begin
    $dumpfile("counter_adv.vcd");
    $dumpvars(0, top);
  end
endmodule
```

### 7.6.1 Ch.5/6 대비 진화 정리

| 항목 | Ch.5 | Ch.6 | Ch.7 |
|------|------|------|------|
| 시나리오 | 드라이버에 하드코딩 | 시퀀스로 분리 | 시퀀스 (동일) |
| 타이밍 | `#1` 해킹 | `#1` 해킹 | **clocking block** |
| 접근 제어 | 없음 | 없음 | **modport** |
| 데이터 전달 | 직접 신호 | seq_item_port | seq_item_port (동일) |
| 모니터 출력 | `uvm_info`만 | `uvm_info`만 | **analysis port** |
| Agent 모드 | 고정 | 고정 | **is_active** |

> **성취감 포인트**: 이제 작성한 테스트벤치는 실무에서 사용하는 것과 **거의 동일한 구조**입니다! 남은 것은 스코어보드(Ch.8), 커버리지(Ch.8), 그리고 고급 시나리오(Ch.9)뿐입니다.

---

## 7.7 체크포인트

### 셀프 체크

**1. TLM port와 analysis port의 차이는?** (7.1)
<details>
<summary>정답 확인</summary>
TLM port(seq_item_port)는 1:1 연결로 드라이버가 시퀀서에게 트랜잭션을 요청합니다. Analysis port는 1:N 브로드캐스트로 모니터가 여러 구독자(스코어보드, 커버리지 등)에게 동시에 데이터를 전송합니다.
</details>

**2. clocking block의 `#1step`이 `#1`보다 나은 이유는?** (7.2)
<details>
<summary>정답 확인</summary>
`#1step`은 타임스케일에 관계없이 항상 이전 타임 슬롯(preponed region)에서 신호를 샘플합니다. IEEE 1800 표준 방법으로 경쟁 조건이 발생하지 않습니다. `#1`은 타임스케일에 의존하고 표준이 아닙니다.
</details>

**3. modport를 사용하는 이유는?** (7.2)
<details>
<summary>정답 확인</summary>
드라이버는 output 신호만, 모니터는 input 신호만 접근하도록 방향성을 제한합니다. 실수로 모니터가 신호를 구동하거나 드라이버가 출력을 읽는 것을 컴파일 타임에 방지합니다.
</details>

**4. get_next_item()과 try_next_item()의 차이는?** (7.3)
<details>
<summary>정답 확인</summary>
get_next_item()은 블로킹으로 트랜잭션이 올 때까지 대기합니다. try_next_item()은 논블로킹으로 즉시 반환하며 없으면 null입니다. 아이들 상태 구동이 필요한 버스 프로토콜에서 try_next_item()을 사용합니다.
</details>

**5. 모니터에서 analysis port의 write()를 호출하면 무슨 일이 일어나나?** (7.4)
<details>
<summary>정답 확인</summary>
연결된 모든 구독자(스코어보드, 커버리지 수집기 등)의 write() 메서드가 자동으로 호출됩니다. 구독자가 없어도 에러가 아닙니다(0:N 가능). 비블로킹으로 실행됩니다.
</details>

**6. Active Agent와 Passive Agent의 차이는?** (7.5)
<details>
<summary>정답 확인</summary>
Active Agent(UVM_ACTIVE)는 Sequencer + Driver + Monitor를 모두 가지고 DUT에 자극을 인가합니다. Passive Agent(UVM_PASSIVE)는 Monitor만 가지고 DUT 신호를 관찰만 합니다. is_active 플래그로 build_phase에서 조건부 생성합니다.
</details>

---

### 연습문제

**[실습 7-1] Clocking block 마이그레이션 (쉬움)** — 약 10분

Chapter 6의 예제 6-1 드라이버에서 `vif.rst_n`, `vif.enable`을 clocking block 방식(`vif.drv_cb.rst_n`, `vif.drv_cb.enable`)으로 변경하세요. 모니터도 `vif.mon_cb`를 사용하도록 수정하세요.

```systemverilog
// 변경 전 (Ch.6 방식)
virtual task drive_item(counter_seq_item item);
  vif.rst_n  <= item.rst_n;       // 직접 접근
  vif.enable <= item.enable;
  repeat(item.cycles) @(posedge vif.clk);
endtask

// 변경 후 (Ch.7 방식) — 여기를 채우세요
virtual task drive_item(counter_seq_item item);
  // TODO: clocking block 사용으로 변경
endtask
```

<details>
<summary>정답 확인</summary>

```systemverilog
virtual task drive_item(counter_seq_item item);
  vif.drv_cb.rst_n  <= item.rst_n;
  vif.drv_cb.enable <= item.enable;
  repeat(item.cycles) @(vif.drv_cb);
endtask
```
</details>

---

**[실습 7-2] Analysis port 연결 (보통)** — 약 15분

모니터의 analysis port를 간단한 subscriber에 연결하세요. subscriber는 트랜잭션을 받을 때마다 카운트를 증가시키고 최종 개수를 출력합니다:

```systemverilog
// 요구사항:
// 1. uvm_subscriber를 상속받는 counter_subscriber 작성
// 2. write() 메서드에서 수신 횟수 카운트
// 3. report_phase()에서 총 수신 트랜잭션 수 출력
// 4. env의 connect_phase에서 monitor.ap → subscriber 연결

class counter_subscriber extends uvm_subscriber #(counter_seq_item);
  `uvm_component_utils(counter_subscriber)

  int tx_count = 0;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  // TODO: write() 구현
  // TODO: report_phase() 구현
endclass
```

<details>
<summary>정답 확인</summary>

```systemverilog
virtual function void write(counter_seq_item t);
  tx_count++;
  `uvm_info(get_type_name(),
    $sformatf("[%0d] %s", tx_count, t.convert2string()), UVM_HIGH)
endfunction

virtual function void report_phase(uvm_phase phase);
  super.report_phase(phase);
  `uvm_info(get_type_name(),
    $sformatf("Total transactions observed: %0d", tx_count), UVM_MEDIUM)
endfunction
```

env의 connect_phase:
```systemverilog
agent.mon.ap.connect(subscriber.analysis_export);
```
</details>

---

**[실습 7-3] Passive Agent 테스트 (도전)** — 약 20분

환경에 두 개의 에이전트를 추가하세요: Active agent (DUT 입력 구동)와 Passive agent (DUT 출력 관찰). Passive agent의 모니터에 subscriber를 연결하여 출력 트랜잭션 수를 세세요.

```systemverilog
// 요구사항:
// 1. counter_env에 input_agent(ACTIVE)와 output_agent(PASSIVE) 추가
// 2. output_agent.mon.ap에 counter_subscriber 연결
// 3. 테스트 실행 후 subscriber의 report에서 총 트랜잭션 수 확인
```

<details>
<summary>정답 확인</summary>

```systemverilog
class counter_env extends uvm_env;
  `uvm_component_utils(counter_env)

  counter_agent input_agent;
  counter_agent output_agent;
  counter_subscriber sub;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    input_agent = counter_agent::type_id::create("input_agent", this);
    input_agent.is_active = UVM_ACTIVE;

    output_agent = counter_agent::type_id::create("output_agent", this);
    output_agent.is_active = UVM_PASSIVE;

    sub = counter_subscriber::type_id::create("sub", this);
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    output_agent.mon.ap.connect(sub.analysis_export);
  endfunction
endclass
```
</details>

---

### 흔한 에러와 해결

| 에러 메시지 | 원인 | 해결 |
|------------|------|------|
| `Cannot drive net` | 모니터에서 output 신호를 구동 시도 | modport 확인, 모니터는 input만 접근 |
| `Port not connected` | connect_phase 누락 | `drv.seq_item_port.connect(sqr.seq_item_export)` 확인 |
| `No write() found` | analysis_imp에 write() 미구현 | 받는 쪽 클래스에 `write()` 함수 구현 |
| `Null object at drv` | Passive agent에서 드라이버 접근 | `get_is_active()` 확인 후 조건부 접근 |
| `Clocking block event` | `@(posedge vif.clk)` 대신 `@(vif.drv_cb)` 미사용 | clocking event로 변경 |

### 용어 정리

| 용어 | 영어 | 설명 |
|------|------|------|
| TLM | Transaction Level Modeling | 컴포넌트 간 트랜잭션 통신 표준 |
| 포트 | Port | 데이터를 보내는 쪽의 연결점 |
| 익스포트 | Export | 데이터를 받는 쪽의 연결점 |
| 분석 포트 | Analysis Port | 1:N 브로드캐스트용 포트 |
| 클럭킹 블록 | Clocking Block | 타이밍 안정적 신호 샘플/구동 |
| 모드포트 | Modport | Interface 신호 접근 방향 제한 |
| 능동 에이전트 | Active Agent | Sequencer + Driver + Monitor 구성 |
| 수동 에이전트 | Passive Agent | Monitor만 구성 |

### 다음 챕터 예고

Chapter 8에서는 이 챕터에서 소개한 analysis port의 **활용**을 본격적으로 다룹니다. **스코어보드(Scoreboard)**로 자동 검증을, **Functional Coverage**로 검증 완전성을 측정합니다.
