# Chapter 13: 고급 시퀀스

> **학습 목표**
> - **가상 시퀀스(Virtual Sequence)**로 여러 에이전트를 동시에 제어할 수 있다
> - **가상 시퀀서(Virtual Sequencer)**를 통한 다중 시퀀서 관리를 이해한다
> - **시퀀스 라이브러리(Sequence Library)**로 테스트 시나리오를 체계적으로 관리할 수 있다
> - **p_sequencer**를 활용해 시퀀스에서 환경 자원에 접근할 수 있다
> - Ch.11 APB 시퀀스와 Ch.12 RAL 시퀀스를 가상 시퀀스로 **조합**할 수 있다

> **선수 지식**: Chapter 6의 기본 시퀀스 패턴(start_item/finish_item, 시퀀스 합성)이 핵심 기반입니다. Chapter 11의 APB 에이전트와 Chapter 12의 RAL 환경을 확장합니다.

---

## 13.1 왜 고급 시퀀스가 필요한가

> **이 절의 목표**: Ch.6 기본 시퀀스의 한계를 이해하고, 고급 시퀀스의 필요성을 파악합니다.

### 13.1.1 Ch.6 방식의 한계 — 단일 에이전트

Ch.6에서 배운 시퀀스 패턴을 떠올려봅시다:

```systemverilog
// Ch.6 방식: 하나의 시퀀서에 하나의 시퀀스
class my_test extends uvm_test;
  virtual task run_phase(uvm_phase phase);
    my_sequence seq = my_sequence::type_id::create("seq");
    phase.raise_objection(this);
    seq.start(env.agent.sqr);  // 시퀀서 하나에 시퀀스 하나
    phase.drop_objection(this);
  endtask
endclass
```

이 패턴은 에이전트가 하나일 때 완벽합니다. 하지만 실무에서는?

| 상황 | Ch.6 방식의 한계 |
|------|-------------------|
| APB + SPI 동시 검증 | 시퀀스 2개를 순차 실행? 동시성 없음 |
| 레지스터 설정 후 데이터 전송 | 두 에이전트의 순서 제어 불가 |
| 인터럽트 발생 + 상태 읽기 | 이벤트 기반 동기화 불가 |
| 에러 주입 + 정상 트래픽 | 독립적 시나리오 조합 불가 |

**핵심 문제**: Ch.6의 시퀀스는 **하나의 시퀀서에 하나의 시나리오**만 실행합니다. 실무 SoC에는 APB, SPI, I2C, UART 등 **여러 에이전트**가 동시에 동작해야 합니다.

### 13.1.2 실무 SoC 검증 — 다중 에이전트 문제

팹리스 회사의 SoC 검증 환경을 상상해봅시다:

```
실무 SoC 검증 환경

┌─────────────────────────────────────────────┐
│  SoC DUT                                    │
│  ┌────────┐  ┌────────┐  ┌────────┐        │
│  │CPU Core│  │ Timer  │  │  UART  │        │
│  └───┬────┘  └───┬────┘  └───┬────┘        │
│      │APB        │APB        │APB           │
│  ════╪═══════════╪═══════════╪══════════    │
│                APB Bus                      │
└─────────────────────────────────────────────┘
       │           │           │
  ┌────┴────┐ ┌────┴────┐ ┌────┴────┐
  │APB Agent│ │APB Agent│ │APB Agent│
  │  #1     │ │  #2     │ │  #3     │
  └─────────┘ └─────────┘ └─────────┘
```

**테스트 시나리오 예시**: "Timer 레지스터를 설정하고 → CPU 코어에 인터럽트를 발생시키고 → UART로 결과를 전송"

이 시나리오를 Ch.6 방식으로 구현하면:

```systemverilog
// Ch.6 방식: 순차 실행 — 동시성 없음, 코드 복잡
virtual task run_phase(uvm_phase phase);
  phase.raise_objection(this);

  // 1단계: Timer 설정 (APB Agent #2)
  timer_seq.start(env.apb_agent2.sqr);

  // 2단계: CPU 인터럽트 (APB Agent #1) — Timer와 동시에 못 함!
  cpu_seq.start(env.apb_agent1.sqr);

  // 3단계: UART 전송 (APB Agent #3)
  uart_seq.start(env.apb_agent3.sqr);

  phase.drop_objection(this);
endtask
```

**문제점:**
1. 세 에이전트가 **순차 실행** — 실제 하드웨어는 동시에 동작
2. 동기화 로직이 **테스트 안에 흩어짐** — 재사용 불가
3. 새 시나리오마다 **테스트를 새로 작성** — 시퀀스 재사용 불가

### 13.1.3 고급 시퀀스 로드맵

이 문제를 해결하는 세 가지 도구가 있습니다:

```
Ch.13 고급 시퀀스 아키텍처

┌─────────────────────────────────────────────┐
│  Virtual Sequence (악보)                     │
│  "Timer 설정 → 인터럽트 → UART 전송"        │
└───────────────────┬─────────────────────────┘
                    │ start()
┌───────────────────▼─────────────────────────┐
│  Virtual Sequencer (지휘자)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ apb_sqr1 │ │ apb_sqr2 │ │ apb_sqr3 │    │
│  └─────┬────┘ └─────┬────┘ └─────┬────┘    │
└────────┼─────────────┼─────────────┼────────┘
         │             │             │
┌────────▼────┐ ┌──────▼──────┐ ┌───▼────────┐
│ APB Agent 1 │ │ APB Agent 2 │ │ APB Agent 3│
│ (CPU)       │ │ (Timer)     │ │ (UART)     │
└─────────────┘ └─────────────┘ └────────────┘
```

| 도구 | 역할 | 비유 |
|------|------|------|
| **Virtual Sequencer** | 여러 시퀀서의 핸들을 모아두는 중앙 허브 | 오케스트라 **지휘자** |
| **Virtual Sequence** | 여러 에이전트에 시나리오를 배포하는 최상위 시퀀스 | **악보** |
| **Sequence Library** | 시퀀스를 모아두고 자동 선택·실행하는 컨테이너 | **플레이리스트** |

> 💡 **비유**: 오케스트라 공연을 생각해보세요. 각 악기 연주자(Agent)는 자기 파트를 연주합니다. 지휘자(Virtual Sequencer)는 모든 악기를 알고 있고, 악보(Virtual Sequence)의 지시에 따라 "바이올린은 지금, 첼로는 4마디 후에" 같은 타이밍을 조율합니다.

---

## 13.2 가상 시퀀서 (Virtual Sequencer)

> **이 절의 목표**: 가상 시퀀서의 개념과 구현 방법을 이해합니다.

### 13.2.1 가상 시퀀서란 — 오케스트라 지휘자

가상 시퀀서는 **트랜잭션을 직접 생성하지 않습니다.** 대신, 여러 실제 시퀀서의 핸들을 모아두는 **중앙 허브** 역할을 합니다.

```
일반 시퀀서 vs 가상 시퀀서

일반 시퀀서 (Ch.6)              가상 시퀀서 (Ch.13)
= "택배 기사"                   = "배차 담당자"
┌──────────────┐               ┌──────────────────────┐
│  Sequencer   │               │  Virtual Sequencer   │
│              │               │                      │
│ seq_item_    │               │ apb_sqr ─────► 핸들  │
│ export ◄─────│── Driver      │ gpio_sqr ────► 핸들  │
│              │               │ spi_sqr ─────► 핸들  │
│ 트랜잭션     │               │                      │
│ 직접 전달    │               │ 트랜잭션 전달 안 함  │
└──────────────┘               └──────────────────────┘
  물건을 직접 배달               택배 기사들을 관리
```

> 💡 **비유**: 일반 시퀀서는 **택배 기사**입니다 — 물건(트랜잭션)을 직접 배달합니다. 가상 시퀀서는 **배차 담당자**입니다 — 물건을 직접 배달하지 않고, 어느 택배 기사에게 보낼지 결정하는 역할입니다.

**핵심 차이**: 일반 시퀀서는 드라이버와 연결되어 트랜잭션을 전달합니다. 가상 시퀀서는 드라이버와 연결되지 않고, **다른 시퀀서들의 핸들만** 가지고 있습니다.

### 13.2.2 가상 시퀀서 구현

Ch.11~12의 APB 환경을 확장하여, APB 에이전트와 GPIO 에이전트를 동시에 제어하는 가상 시퀀서를 만들겠습니다. 먼저 간단한 GPIO 에이전트를 가정합니다.

```systemverilog
// 간단한 GPIO 시퀀스 아이템 (가상 시퀀스 데모용)
class gpio_seq_item extends uvm_sequence_item;
  `uvm_object_utils(gpio_seq_item)

  rand bit [7:0] gpio_data;
  rand bit        gpio_dir;   // 0: input, 1: output

  function new(string name = "gpio_seq_item");
    super.new(name);
  endfunction

  function string convert2string();
    return $sformatf("dir=%0b data=0x%02h", gpio_dir, gpio_data);
  endfunction
endclass

// GPIO 시퀀서 — 일반 시퀀서
typedef uvm_sequencer#(gpio_seq_item) gpio_sequencer;
```

이제 가상 시퀀서를 구현합니다:

```systemverilog
// ============================================================
// 가상 시퀀서: 여러 시퀀서의 핸들을 모아두는 중앙 허브
// ============================================================
class apb_virtual_sequencer extends uvm_sequencer;
  `uvm_component_utils(apb_virtual_sequencer)

  // ---- 실제 시퀀서 핸들 ----
  uvm_sequencer#(apb_seq_item)  apb_sqr;    // APB 시퀀서 (Ch.11)
  gpio_sequencer               gpio_sqr;    // GPIO 시퀀서

  // ---- 선택사항: RAL 모델 핸들 (Ch.12 연동) ----
  apb_reg_block                reg_model;   // RAL 모델

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  // 가상 시퀀서는 build_phase/connect_phase가 필요 없습니다.
  // 핸들은 상위 환경(env)에서 할당합니다.
endclass
```

**주의할 점:**
- 가상 시퀀서는 `uvm_sequencer`를 **파라미터 없이** 상속합니다 — 왜? 일반 시퀀서는 `uvm_sequencer#(apb_seq_item)`처럼 트랜잭션 타입을 지정하여 드라이버에 트랜잭션을 전달합니다. 가상 시퀀서는 **트랜잭션을 직접 전달하지 않으므로** 타입 파라미터가 불필요합니다. 핸들만 보관하는 "허브" 역할이기 때문입니다.
- 실제 시퀀서의 **핸들만 선언** — 생성(create)은 하지 않습니다
- 핸들 할당은 **상위 환경의 connect_phase**에서 수행합니다

### 13.2.3 환경에 가상 시퀀서 통합

Ch.12의 `apb_ral_env`를 확장하여 가상 시퀀서를 추가합니다:

```systemverilog
// ============================================================
// 확장된 환경: 가상 시퀀서 포함
// ============================================================
class apb_virtual_env extends uvm_env;
  `uvm_component_utils(apb_virtual_env)

  // ---- 기존 컴포넌트 (Ch.11~12) ----
  apb_agent           apb_agt;        // APB 에이전트
  apb_reg_block       reg_model;      // RAL 모델
  apb_reg_adapter     adapter;        // Adapter
  uvm_reg_predictor#(apb_seq_item) predictor;  // Predictor

  // ---- 새로 추가 ----
  gpio_sequencer      gpio_sqr;       // GPIO 시퀀서 (간략화)
  apb_virtual_sequencer  v_sqr;       // 가상 시퀀서

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  // build_phase: 모든 컴포넌트 생성
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // 기존 컴포넌트 생성
    apb_agt   = apb_agent::type_id::create("apb_agt", this);
    reg_model = apb_reg_block::type_id::create("reg_model");
    reg_model.build();
    reg_model.lock_model();
    adapter   = apb_reg_adapter::type_id::create("adapter");
    predictor = uvm_reg_predictor#(apb_seq_item)::type_id::create("predictor", this);

    // 새 컴포넌트 생성
    gpio_sqr = gpio_sequencer::type_id::create("gpio_sqr", this);
    v_sqr    = apb_virtual_sequencer::type_id::create("v_sqr", this);
  endfunction

  // connect_phase: 핸들 연결 — 가상 시퀀서의 핵심!
  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);

    // 기존 RAL 연결 (Ch.12)
    reg_model.reg_map.set_sequencer(apb_agt.sqr, adapter);
    reg_model.reg_map.set_auto_predict(0);
    predictor.map     = reg_model.reg_map;
    predictor.adapter = adapter;
    apb_agt.mon.ap.connect(predictor.bus_in);

    // ★ 가상 시퀀서에 실제 시퀀서 핸들 할당 ★
    v_sqr.apb_sqr   = apb_agt.sqr;      // APB 시퀀서 연결
    v_sqr.gpio_sqr  = gpio_sqr;         // GPIO 시퀀서 연결
    v_sqr.reg_model = reg_model;         // RAL 모델 전달
  endfunction
endclass
```

**핵심 3줄** — 가상 시퀀서 연결:

```systemverilog
v_sqr.apb_sqr   = apb_agt.sqr;    // APB 시퀀서 핸들
v_sqr.gpio_sqr  = gpio_sqr;       // GPIO 시퀀서 핸들
v_sqr.reg_model = reg_model;       // RAL 모델 핸들
```

이 연결이 완료되면, 가상 시퀀스에서 `p_sequencer.apb_sqr`로 APB 시퀀서에 접근할 수 있습니다.

> 💡 **비유**: 오케스트라 지휘자(Virtual Sequencer)가 공연장에 도착했습니다. 매니저(환경의 connect_phase)가 "바이올린은 저쪽, 첼로는 이쪽"하고 각 악기 연주자의 위치(핸들)를 알려줍니다.

> ⚠️ **흔한 실수**: 가상 시퀀서의 핸들을 build_phase에서 할당하면 안 됩니다. 실제 시퀀서가 아직 생성되지 않았을 수 있습니다. **반드시 connect_phase에서** 할당하세요.

---

## 13.3 가상 시퀀스 (Virtual Sequence)

> **이 절의 목표**: 가상 시퀀스를 구현하고 p_sequencer를 활용하는 방법을 배웁니다.

### 13.3.1 가상 시퀀스란 — 악보

가상 시퀀스는 **가상 시퀀서 위에서 실행**되는 시퀀스입니다. 일반 시퀀스와 달리, 트랜잭션을 직접 생성하지 않고 **하위 시퀀스를 여러 시퀀서에 배포**합니다.

```
일반 시퀀스 (Ch.6)                    가상 시퀀스 (Ch.13)

┌─────────────┐                     ┌──────────────────────┐
│ my_sequence  │                     │ virtual_sequence     │
│              │                     │                      │
│ body() {     │                     │ body() {             │
│   start_item │                     │   apb_seq.start(     │
│   finish_item│                     │     p_sqr.apb_sqr);  │
│ }            │                     │   gpio_seq.start(    │
│              │                     │     p_sqr.gpio_sqr); │
│ ↓ 트랜잭션  │                     │ }                    │
│ 직접 생성    │                     │ ↓ 하위 시퀀스 배포   │
└──────┬──────┘                     └──────────┬───────────┘
       │                                       │
  ┌────▼────┐                          ┌───────▼───────┐
  │sequencer│                          │virtual_sequencer│
  └─────────┘                          └───────────────┘
```

### 13.3.2 가상 시퀀스 구현

먼저 기본 APB 시퀀스들을 준비합니다 (Ch.11에서 만든 것 활용):

```systemverilog
// APB Write 시퀀스 (Ch.11 복습)
class apb_write_seq extends uvm_sequence#(apb_seq_item);
  `uvm_object_utils(apb_write_seq)

  rand bit [3:0] addr;
  rand bit [7:0] data;

  function new(string name = "apb_write_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_seq_item req;
    req = apb_seq_item::type_id::create("req");
    start_item(req);
    if (!req.randomize() with { paddr == addr; pwdata == data; pwrite == 1; })
      `uvm_error(get_type_name(), "Randomization failed")
    finish_item(req);
    `uvm_info(get_type_name(), $sformatf("APB Write: addr=0x%0h data=0x%02h", addr, data), UVM_MEDIUM)
  endtask
endclass

// APB Read 시퀀스 (Ch.11 복습)
class apb_read_seq extends uvm_sequence#(apb_seq_item);
  `uvm_object_utils(apb_read_seq)

  rand bit [3:0] addr;

  function new(string name = "apb_read_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_seq_item req;
    req = apb_seq_item::type_id::create("req");
    start_item(req);
    if (!req.randomize() with { paddr == addr; pwrite == 0; })
      `uvm_error(get_type_name(), "Randomization failed")
    finish_item(req);
    `uvm_info(get_type_name(), $sformatf("APB Read: addr=0x%0h", addr), UVM_MEDIUM)
  endtask
endclass

// GPIO 출력 시퀀스
class gpio_output_seq extends uvm_sequence#(gpio_seq_item);
  `uvm_object_utils(gpio_output_seq)

  rand bit [7:0] out_data;

  function new(string name = "gpio_output_seq");
    super.new(name);
  endfunction

  virtual task body();
    gpio_seq_item req;
    req = gpio_seq_item::type_id::create("req");
    start_item(req);
    if (!req.randomize() with { gpio_dir == 1; gpio_data == out_data; })
      `uvm_error(get_type_name(), "Randomization failed")
    finish_item(req);
    `uvm_info(get_type_name(), $sformatf("GPIO Output: data=0x%02h", out_data), UVM_MEDIUM)
  endtask
endclass
```

이제 가상 시퀀스를 만듭니다:

```systemverilog
// ============================================================
// 가상 시퀀스: APB + GPIO를 동시에 제어
// ============================================================
class apb_gpio_virtual_seq extends uvm_sequence;
  `uvm_object_utils(apb_gpio_virtual_seq)
  `uvm_declare_p_sequencer(apb_virtual_sequencer)  // ★ 핵심!

  function new(string name = "apb_gpio_virtual_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_write_seq   apb_wr;
    apb_read_seq    apb_rd;
    gpio_output_seq gpio_out;

    // 시퀀스 생성
    apb_wr   = apb_write_seq::type_id::create("apb_wr");
    apb_rd   = apb_read_seq::type_id::create("apb_rd");
    gpio_out = gpio_output_seq::type_id::create("gpio_out");

    `uvm_info(get_type_name(), "=== 가상 시퀀스 시작 ===", UVM_LOW)

    // ---- 시나리오 1: 순차 실행 ----
    `uvm_info(get_type_name(), "--- 1단계: APB 레지스터 설정 ---", UVM_MEDIUM)
    apb_wr.addr = 4'h0;
    apb_wr.data = 8'h85;  // ctrl_reg: enable=1, mode=00
    apb_wr.start(p_sequencer.apb_sqr);  // ★ APB 시퀀서에 배포

    `uvm_info(get_type_name(), "--- 2단계: GPIO 출력 ---", UVM_MEDIUM)
    gpio_out.out_data = 8'hAA;
    gpio_out.start(p_sequencer.gpio_sqr);  // ★ GPIO 시퀀서에 배포

    // ---- 시나리오 2: 병렬 실행 ----
    `uvm_info(get_type_name(), "--- 3단계: APB + GPIO 동시 실행 ---", UVM_MEDIUM)
    fork
      begin  // APB: 레지스터 읽기
        apb_rd.addr = 4'h0;
        apb_rd.start(p_sequencer.apb_sqr);
      end
      begin  // GPIO: 다른 데이터 출력
        gpio_output_seq gpio_out2;
        gpio_out2 = gpio_output_seq::type_id::create("gpio_out2");
        gpio_out2.out_data = 8'h55;
        gpio_out2.start(p_sequencer.gpio_sqr);
      end
    join

    `uvm_info(get_type_name(), "=== 가상 시퀀스 완료 ===", UVM_LOW)
  endtask
endclass
```

**코드 해부:**

| 요소 | 설명 |
|------|------|
| `uvm_declare_p_sequencer` | 가상 시퀀서 타입을 `p_sequencer`로 캐스팅 |
| `p_sequencer.apb_sqr` | 가상 시퀀서를 통해 APB 시퀀서에 접근 |
| `sub_seq.start(target_sqr)` | 하위 시퀀스를 특정 시퀀서에서 실행 |
| `fork...join` | 여러 시퀀스를 **병렬 실행** |

**fork 변형 — 실무에서 자주 쓰는 3가지:**

| 구문 | 동작 | 실무 용도 |
|------|------|-----------|
| `fork...join` | 모든 블록이 끝날 때까지 대기 | 동시 트래픽 생성 (가장 일반적) |
| `fork...join_any` | 하나라도 끝나면 계속 진행 | 타임아웃 패턴 (시퀀스 + 워치독) |
| `fork...join_none` | 대기 없이 즉시 다음 진행 | 백그라운드 모니터링, 비동기 이벤트 |

```systemverilog
// fork...join_any 예: 타임아웃 패턴
fork
  begin  // 정상 시퀀스
    apb_wr.start(p_sequencer.apb_sqr);
  end
  begin  // 워치독 타이머
    #10000;
    `uvm_error("TIMEOUT", "APB 시퀀스 타임아웃!")
  end
join_any
disable fork;  // 남은 프로세스 정리

// fork...join_none 예: 백그라운드 GPIO 토글
fork
  begin  // 백그라운드에서 GPIO 계속 토글
    forever begin
      gpio_out.start(p_sequencer.gpio_sqr);
      #100;
    end
  end
join_none
// APB 시퀀스는 독립적으로 계속 진행
apb_wr.start(p_sequencer.apb_sqr);
```

> ⚠️ **주의**: `fork...join_any` 사용 후에는 `disable fork`로 남은 프로세스를 정리하세요. 그렇지 않으면 좀비 프로세스가 시뮬레이션 끝까지 실행됩니다.

### 13.3.3 p_sequencer로 시퀀서 접근

`p_sequencer`는 UVM 시퀀스에서 가장 중요한 고급 기능입니다. 기본 개념을 정리합니다.

**m_sequencer vs p_sequencer:**

```systemverilog
// m_sequencer — 모든 시퀀스에 기본 제공 (uvm_sequencer_base 타입)
class uvm_sequence extends uvm_sequence_base;
  protected uvm_sequencer_base m_sequencer;  // 기본 핸들
  // m_sequencer로는 커스텀 필드에 접근 불가!
endclass

// p_sequencer — uvm_declare_p_sequencer로 선언 (캐스팅된 타입)
`uvm_declare_p_sequencer(apb_virtual_sequencer)
// 내부적으로:
// apb_virtual_sequencer p_sequencer;
// p_sequencer = $cast(m_sequencer);  (자동 캐스팅)
```

| 비교 | m_sequencer | p_sequencer |
|------|-------------|-------------|
| 타입 | `uvm_sequencer_base` | 사용자 지정 (예: `apb_virtual_sequencer`) |
| 기본 제공 | ✅ 항상 있음 | ❌ 선언 필요 |
| 커스텀 필드 접근 | ❌ 불가 | ✅ 가능 (`.apb_sqr`, `.reg_model` 등) |
| 사용 시점 | 일반 시퀀스 | 가상 시퀀스, 환경 자원 접근 시 |

> ⚠️ **p_sequencer의 장단점**:
> - **장점**: 시퀀스에서 환경의 시퀀서, RAL 모델 등에 직접 접근 가능
> - **단점**: 시퀀스가 특정 시퀀서 타입에 **의존** — 재사용성 감소
> - **대안**: `uvm_config_db`로 핸들을 전달하는 방법도 있음 (13.5.2에서 설명)

### 13.3.4 첫 가상 시퀀스 시뮬레이션

테스트에서 가상 시퀀스를 실행합니다:

```systemverilog
// ============================================================
// 가상 시퀀스 테스트
// ============================================================
class apb_gpio_virtual_test extends uvm_test;
  `uvm_component_utils(apb_gpio_virtual_test)

  apb_virtual_env env;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = apb_virtual_env::type_id::create("env", this);
  endfunction

  virtual task run_phase(uvm_phase phase);
    apb_gpio_virtual_seq vseq;
    vseq = apb_gpio_virtual_seq::type_id::create("vseq");

    phase.raise_objection(this);
    vseq.start(env.v_sqr);  // ★ 가상 시퀀서에서 시작!
    phase.drop_objection(this);
  endtask
endclass
```

**시뮬레이션 결과 (예상):**

```
UVM_INFO @ 0: uvm_test_top [apb_gpio_virtual_seq] === 가상 시퀀스 시작 ===
UVM_INFO @ 10: uvm_test_top [apb_gpio_virtual_seq] --- 1단계: APB 레지스터 설정 ---
UVM_INFO @ 30: uvm_test_top.env.apb_agt [apb_write_seq] APB Write: addr=0x0 data=0x85
UVM_INFO @ 30: uvm_test_top [apb_gpio_virtual_seq] --- 2단계: GPIO 출력 ---
UVM_INFO @ 40: uvm_test_top [gpio_output_seq] GPIO Output: data=0xaa
UVM_INFO @ 40: uvm_test_top [apb_gpio_virtual_seq] --- 3단계: APB + GPIO 동시 실행 ---
UVM_INFO @ 60: uvm_test_top.env.apb_agt [apb_read_seq] APB Read: addr=0x0
UVM_INFO @ 50: uvm_test_top [gpio_output_seq] GPIO Output: data=0x55
UVM_INFO @ 60: uvm_test_top [apb_gpio_virtual_seq] === 가상 시퀀스 완료 ===
```

**주목**: 3단계에서 APB Read(@60)와 GPIO Output(@50)이 **동시에 실행**됩니다. `fork...join`으로 병렬 실행이 가능해졌습니다.

> 🔧 **트러블슈팅**: 가상 시퀀스 실행 시 자주 발생하는 오류:

| 오류 | 원인 | 해결 |
|------|------|------|
| `p_sequencer is null` | `uvm_declare_p_sequencer` 누락 | 매크로 추가 확인 |
| `Null object access on sqr` | connect_phase에서 핸들 미할당 | `v_sqr.apb_sqr = ...` 확인 |
| `Sequence not compatible` | 시퀀스-시퀀서 타입 불일치 | `start()` 인자의 시퀀서 타입 확인 |

---

## 13.4 시퀀스 라이브러리 (Sequence Library)

> **이 절의 목표**: 시퀀스 라이브러리로 다양한 시퀀스를 체계적으로 관리하는 방법을 배웁니다.

### 13.4.1 왜 시퀀스 라이브러리가 필요한가

프로젝트가 커지면 시퀀스도 많아집니다:

```
프로젝트 시퀀스 목록 (예시)

apb_write_seq         — APB 쓰기
apb_read_seq          — APB 읽기
apb_write_read_seq    — 쓰기 후 읽기 검증
apb_burst_seq         — 연속 쓰기
apb_random_seq        — 랜덤 트래픽
apb_error_seq         — 에러 시나리오
apb_reset_seq         — 리셋 시퀀스
...
```

테스트마다 "이번에는 어떤 시퀀스를 쓸까?"를 결정하고 코드에 하드코딩하는 것은 비효율적입니다. **시퀀스 라이브러리**는 시퀀스를 등록해두고, 실행 시 자동으로 선택·실행하는 컨테이너입니다.

> 💡 **비유**: 음악 앱의 **플레이리스트**를 생각해보세요. 노래(시퀀스)를 등록하고, "순서대로 재생", "랜덤 재생", "한 곡 반복" 같은 모드를 선택할 수 있습니다.

### 13.4.2 uvm_sequence_library 구현

```systemverilog
// ============================================================
// APB 시퀀스 라이브러리
// ============================================================
class apb_seq_library extends uvm_sequence_library#(apb_seq_item);
  `uvm_object_utils(apb_seq_library)
  `uvm_sequence_library_utils(apb_seq_library)

  function new(string name = "apb_seq_library");
    super.new(name);

    // 라이브러리 초기화 — 반드시 호출!
    init_sequence_library();
  endfunction
endclass
```

시퀀스를 라이브러리에 등록합니다:

```systemverilog
// 등록할 시퀀스 1: APB 쓰기
class apb_write_lib_seq extends uvm_sequence#(apb_seq_item);
  `uvm_object_utils(apb_write_lib_seq)
  `uvm_add_to_seq_lib(apb_write_lib_seq, apb_seq_library)  // ★ 등록!

  function new(string name = "apb_write_lib_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_seq_item req;
    req = apb_seq_item::type_id::create("req");
    start_item(req);
    if (!req.randomize() with { pwrite == 1; })
      `uvm_error(get_type_name(), "Randomization failed")
    finish_item(req);
    `uvm_info(get_type_name(), $sformatf("LIB Write: addr=0x%0h data=0x%02h",
              req.paddr, req.pwdata), UVM_MEDIUM)
  endtask
endclass

// 등록할 시퀀스 2: APB 읽기
class apb_read_lib_seq extends uvm_sequence#(apb_seq_item);
  `uvm_object_utils(apb_read_lib_seq)
  `uvm_add_to_seq_lib(apb_read_lib_seq, apb_seq_library)  // ★ 등록!

  function new(string name = "apb_read_lib_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_seq_item req;
    req = apb_seq_item::type_id::create("req");
    start_item(req);
    if (!req.randomize() with { pwrite == 0; })
      `uvm_error(get_type_name(), "Randomization failed")
    finish_item(req);
    `uvm_info(get_type_name(), $sformatf("LIB Read: addr=0x%0h", req.paddr), UVM_MEDIUM)
  endtask
endclass

// 등록할 시퀀스 3: 쓰기 후 읽기 검증
class apb_write_read_lib_seq extends uvm_sequence#(apb_seq_item);
  `uvm_object_utils(apb_write_read_lib_seq)
  `uvm_add_to_seq_lib(apb_write_read_lib_seq, apb_seq_library)  // ★ 등록!

  function new(string name = "apb_write_read_lib_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_seq_item wr_req, rd_req;
    bit [3:0] target_addr;
    bit [7:0] target_data;

    // 주소와 데이터를 미리 결정
    target_addr = $urandom_range(0, 15);
    target_data = $urandom_range(0, 255);

    // 쓰기
    wr_req = apb_seq_item::type_id::create("wr_req");
    start_item(wr_req);
    if (!wr_req.randomize() with { paddr == target_addr; pwdata == target_data; pwrite == 1; })
      `uvm_error(get_type_name(), "Randomization failed")
    finish_item(wr_req);

    // 읽기
    rd_req = apb_seq_item::type_id::create("rd_req");
    start_item(rd_req);
    if (!rd_req.randomize() with { paddr == target_addr; pwrite == 0; })
      `uvm_error(get_type_name(), "Randomization failed")
    finish_item(rd_req);

    `uvm_info(get_type_name(), $sformatf("LIB WriteRead: addr=0x%0h write=0x%02h",
              target_addr, target_data), UVM_MEDIUM)
  endtask
endclass
```

### 13.4.3 시퀀스 선택 모드

시퀀스 라이브러리의 핵심은 **선택 모드**입니다. 4가지 모드를 제공합니다:

| 모드 | 상수 | 동작 | 비유 |
|------|------|------|------|
| 모드 | 상수 | 동작 | 비유 |
|------|------|------|------|
| **Random** | `UVM_SEQ_LIB_RAND` | 등록된 시퀀스 중 랜덤 선택 (중복 허용) | 셔플 재생 (같은 곡 반복 가능) |
| **Random Cycle** | `UVM_SEQ_LIB_RANDC` | 모든 시퀀스를 한 번씩 랜덤 순서로 실행 | 셔플 재생 (중복 없음) |
| **Item** | `UVM_SEQ_LIB_ITEM` | 시퀀스 없이 트랜잭션을 직접 랜덤 생성 | 즉석 연주 |
| **User** | `UVM_SEQ_LIB_USER` | 사용자 정의 선택 로직 | 수동 재생 |

**실무 추천 — 언제 어떤 모드를 쓸까?**

| 모드 | 추천 상황 | 이유 |
|------|-----------|------|
| `RANDC` | **커버리지 수집** (가장 많이 사용) | 모든 시퀀스가 한 번씩 실행되어 빠짐없이 커버리지 달성 |
| `RAND` | **스트레스 테스트** | 특정 시퀀스가 집중적으로 반복될 수 있어 코너 케이스 발견에 유리 |
| `ITEM` | **초기 검증, 스모크 테스트** | 시퀀스 로직 없이 트랜잭션만 빠르게 생성하여 기본 동작 확인 |
| `USER` | **특수 시나리오** (에러 주입 순서 등) | 정확한 실행 순서가 필요한 경우 사용자 로직으로 제어 |

테스트에서 시퀀스 라이브러리를 사용하는 방법:

```systemverilog
// ============================================================
// 시퀀스 라이브러리 테스트
// ============================================================
class apb_seq_lib_test extends uvm_test;
  `uvm_component_utils(apb_seq_lib_test)

  apb_virtual_env env;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = apb_virtual_env::type_id::create("env", this);
  endfunction

  virtual task run_phase(uvm_phase phase);
    apb_seq_library seq_lib;
    seq_lib = apb_seq_library::type_id::create("seq_lib");

    phase.raise_objection(this);

    // ---- 모드 설정 ----
    seq_lib.selection_mode = UVM_SEQ_LIB_RANDC;  // 모든 시퀀스 한 번씩
    seq_lib.min_random_count = 5;   // 최소 5회 실행
    seq_lib.max_random_count = 10;  // 최대 10회 실행

    `uvm_info(get_type_name(), $sformatf("시퀀스 라이브러리: %0d개 시퀀스 등록됨",
              seq_lib.sequences.size()), UVM_LOW)

    // ---- 실행 ----
    seq_lib.start(env.apb_agt.sqr);  // APB 시퀀서에서 실행

    phase.drop_objection(this);
  endtask
endclass
```

**시뮬레이션 결과 (예상, RANDC 모드):**

```
UVM_INFO @ 0: [apb_seq_lib_test] 시퀀스 라이브러리: 3개 시퀀스 등록됨
UVM_INFO @ 20: [apb_write_lib_seq] LIB Write: addr=0x3 data=0xa7
UVM_INFO @ 40: [apb_write_read_lib_seq] LIB WriteRead: addr=0xb write=0x42
UVM_INFO @ 80: [apb_read_lib_seq] LIB Read: addr=0x7
UVM_INFO @ 100: [apb_read_lib_seq] LIB Read: addr=0x2
UVM_INFO @ 120: [apb_write_lib_seq] LIB Write: addr=0xf data=0x19
... (5~10회 반복)
```

**RANDC 모드**에서는 3개 시퀀스가 모두 한 번씩 실행된 후, 다시 랜덤 순서로 반복됩니다. 특정 시퀀스가 빠지는 일이 없으므로 **커버리지 달성에 유리**합니다.

> 🔧 **트러블슈팅**: 시퀀스 라이브러리 관련 오류:

| 오류 | 원인 | 해결 |
|------|------|------|
| `No sequences registered` | `uvm_add_to_seq_lib` 누락 | 각 시퀀스에 매크로 추가 |
| `init_sequence_library not called` | 생성자에서 초기화 누락 | `init_sequence_library()` 호출 추가 |
| `Type mismatch` | 시퀀스와 라이브러리의 seq_item 타입 불일치 | 제네릭 파라미터 확인 |

---

## 13.5 고급 시퀀스 패턴

> **이 절의 목표**: 실무에서 자주 사용하는 고급 시퀀스 패턴을 학습합니다.

### 13.5.1 계층적 시퀀스 (Layered Sequences)

Ch.6에서 마스터 시퀀스(여러 서브 시퀀스를 순차 실행)를 배웠습니다. 계층적 시퀀스는 이를 **기능 단위**로 확장합니다.

```systemverilog
// ============================================================
// 계층적 시퀀스: 기능별 분리
// ============================================================

// 1단계: 레지스터 초기화 시퀀스
class apb_init_seq extends uvm_sequence#(apb_seq_item);
  `uvm_object_utils(apb_init_seq)

  function new(string name = "apb_init_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_write_seq wr;

    `uvm_info(get_type_name(), "--- 레지스터 초기화 시작 ---", UVM_MEDIUM)

    // ctrl_reg 초기화: enable=1, mode=00
    wr = apb_write_seq::type_id::create("wr");
    wr.addr = 4'h0;
    wr.data = 8'h80;  // enable=1
    wr.start(m_sequencer);

    // data_reg 초기화: 0x00
    wr = apb_write_seq::type_id::create("wr");
    wr.addr = 4'h2;
    wr.data = 8'h00;
    wr.start(m_sequencer);

    `uvm_info(get_type_name(), "--- 레지스터 초기화 완료 ---", UVM_MEDIUM)
  endtask
endclass

// 2단계: 데이터 전송 시퀀스
class apb_data_xfer_seq extends uvm_sequence#(apb_seq_item);
  `uvm_object_utils(apb_data_xfer_seq)

  rand int unsigned num_transfers;

  constraint c_transfers { num_transfers inside {[3:8]}; }

  function new(string name = "apb_data_xfer_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_write_seq wr;

    `uvm_info(get_type_name(), $sformatf("--- 데이터 전송: %0d회 ---", num_transfers), UVM_MEDIUM)

    repeat(num_transfers) begin
      wr = apb_write_seq::type_id::create("wr");
      wr.addr = 4'h2;  // data_reg
      // data는 랜덤
      wr.start(m_sequencer);
    end
  endtask
endclass

// 3단계: 검증 시퀀스
class apb_verify_seq extends uvm_sequence#(apb_seq_item);
  `uvm_object_utils(apb_verify_seq)

  function new(string name = "apb_verify_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_read_seq rd;

    `uvm_info(get_type_name(), "--- 레지스터 검증 시작 ---", UVM_MEDIUM)

    // status_reg 읽기
    rd = apb_read_seq::type_id::create("rd");
    rd.addr = 4'h1;
    rd.start(m_sequencer);

    // ctrl_reg 읽기 (설정 확인)
    rd = apb_read_seq::type_id::create("rd");
    rd.addr = 4'h0;
    rd.start(m_sequencer);

    `uvm_info(get_type_name(), "--- 레지스터 검증 완료 ---", UVM_MEDIUM)
  endtask
endclass

// ============================================================
// 마스터 시퀀스: 계층적 조합
// ============================================================
class apb_master_scenario_seq extends uvm_sequence#(apb_seq_item);
  `uvm_object_utils(apb_master_scenario_seq)

  function new(string name = "apb_master_scenario_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_init_seq       init;
    apb_data_xfer_seq  xfer;
    apb_verify_seq     verify;

    `uvm_info(get_type_name(), "=== 마스터 시나리오 시작 ===", UVM_LOW)

    // 1단계: 초기화
    init = apb_init_seq::type_id::create("init");
    init.start(m_sequencer);

    // 2단계: 데이터 전송
    xfer = apb_data_xfer_seq::type_id::create("xfer");
    xfer.start(m_sequencer);

    // 3단계: 검증
    verify = apb_verify_seq::type_id::create("verify");
    verify.start(m_sequencer);

    `uvm_info(get_type_name(), "=== 마스터 시나리오 완료 ===", UVM_LOW)
  endtask
endclass
```

**계층적 시퀀스의 장점:**

| 장점 | 설명 |
|------|------|
| **재사용성** | `apb_init_seq`을 다른 테스트에서도 사용 가능 |
| **유지보수** | 초기화 로직 변경 시 `apb_init_seq`만 수정 |
| **가독성** | 마스터 시퀀스가 "초기화 → 전송 → 검증" 흐름을 명확히 보여줌 |
| **조합** | 서브 시퀀스를 자유롭게 조합하여 새 시나리오 생성 |

### 13.5.2 시퀀스와 config_db 연동

`p_sequencer` 대신 `uvm_config_db`를 사용하여 시퀀스에 자원을 전달하는 패턴입니다. 이 방법은 시퀀스의 **재사용성을 높입니다.**

```systemverilog
// ============================================================
// config_db를 사용한 시퀀스 자원 접근
// ============================================================
class apb_configurable_seq extends uvm_sequence#(apb_seq_item);
  `uvm_object_utils(apb_configurable_seq)

  // 외부에서 설정할 파라미터
  int unsigned repeat_count = 5;
  bit [3:0]   target_addr   = 4'h0;

  function new(string name = "apb_configurable_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_seq_item req;

    // config_db에서 설정 가져오기 (선택적)
    void'(uvm_config_db#(int)::get(null, get_full_name(),
          "repeat_count", repeat_count));
    void'(uvm_config_db#(bit[3:0])::get(null, get_full_name(),
          "target_addr", target_addr));

    `uvm_info(get_type_name(), $sformatf("Config: repeat=%0d, addr=0x%0h",
              repeat_count, target_addr), UVM_MEDIUM)

    repeat(repeat_count) begin
      req = apb_seq_item::type_id::create("req");
      start_item(req);
      if (!req.randomize() with { paddr == target_addr; pwrite == 1; })
        `uvm_error(get_type_name(), "Randomization failed")
      finish_item(req);
    end
  endtask
endclass
```

테스트에서 config_db로 설정:

```systemverilog
// 테스트에서 시퀀스 파라미터 설정
class apb_config_test extends uvm_test;
  // ...
  virtual task run_phase(uvm_phase phase);
    apb_configurable_seq seq;
    seq = apb_configurable_seq::type_id::create("seq");

    phase.raise_objection(this);

    // config_db로 시퀀스 파라미터 설정
    uvm_config_db#(int)::set(this, "env.apb_agt.sqr.seq",
                              "repeat_count", 10);
    uvm_config_db#(bit[3:0])::set(this, "env.apb_agt.sqr.seq",
                                   "target_addr", 4'h5);

    seq.start(env.apb_agt.sqr);

    phase.drop_objection(this);
  endtask
endclass
```

**p_sequencer vs config_db 비교:**

| 비교 | p_sequencer | config_db |
|------|-------------|-----------|
| **결합도** | 강함 (특정 시퀀서 타입 의존) | 약함 (문자열 키 기반) |
| **성능** | 빠름 (직접 접근) | 느림 (해시 테이블 검색) |
| **디버깅** | 쉬움 (타입 체크) | 어려움 (런타임 오류) |
| **재사용성** | 낮음 | 높음 |
| **추천 용도** | 가상 시퀀스 | 설정 파라미터 전달 |

### 13.5.3 시퀀스에서 RAL 사용

Ch.12에서 배운 RAL을 가상 시퀀스에서 활용하는 패턴입니다. 두 가지 방법이 있습니다.

**방법 1: p_sequencer를 통한 RAL 접근 (가상 시퀀스)**

```systemverilog
// ============================================================
// 가상 시퀀스에서 RAL 사용
// ============================================================
class apb_ral_virtual_seq extends uvm_sequence;
  `uvm_object_utils(apb_ral_virtual_seq)
  `uvm_declare_p_sequencer(apb_virtual_sequencer)

  function new(string name = "apb_ral_virtual_seq");
    super.new(name);
  endfunction

  virtual task body();
    uvm_status_e   status;
    uvm_reg_data_t value;
    apb_reg_block  model;

    // p_sequencer를 통해 RAL 모델 접근
    model = p_sequencer.reg_model;

    `uvm_info(get_type_name(), "=== RAL 가상 시퀀스 시작 ===", UVM_LOW)

    // RAL로 레지스터 쓰기 (Frontdoor)
    model.ctrl_reg.write(status, 8'h85, .parent(this));
    if (status != UVM_IS_OK)
      `uvm_error(get_type_name(), "ctrl_reg write failed")

    `uvm_info(get_type_name(), "ctrl_reg 설정 완료: enable=1, mode=00", UVM_MEDIUM)

    // RAL로 레지스터 읽기
    model.status_reg.read(status, value, .parent(this));
    `uvm_info(get_type_name(), $sformatf("status_reg = 0x%02h", value), UVM_MEDIUM)

    // 필드 레벨 접근
    model.ctrl_reg.enable.set(1'b0);   // desired 값 변경
    model.ctrl_reg.update(status, .parent(this));  // DUT에 반영

    `uvm_info(get_type_name(), "=== RAL 가상 시퀀스 완료 ===", UVM_LOW)
  endtask
endclass
```

**방법 2: uvm_reg_sequence 상속 (일반 시퀀스)**

```systemverilog
// ============================================================
// uvm_reg_sequence 상속으로 RAL 사용
// ============================================================
class apb_ral_check_seq extends uvm_reg_sequence;
  `uvm_object_utils(apb_ral_check_seq)

  // uvm_reg_sequence는 'model' 프로퍼티를 제공
  // → 테스트에서 seq.model = reg_model; 로 할당

  function new(string name = "apb_ral_check_seq");
    super.new(name);
  endfunction

  virtual task body();
    uvm_status_e   status;
    uvm_reg_data_t value;

    // model 프로퍼티로 RAL 접근 (p_sequencer 불필요!)
    model.ctrl_reg.write(status, 8'hA0, .parent(this));
    model.ctrl_reg.read(status, value, .parent(this));

    if (value != 8'hA0)
      `uvm_error(get_type_name(), $sformatf("Mismatch: expected=0xA0, got=0x%02h", value))
    else
      `uvm_info(get_type_name(), "ctrl_reg read-back 검증 성공!", UVM_LOW)
  endtask
endclass

// 테스트에서 사용:
// apb_ral_check_seq seq = apb_ral_check_seq::type_id::create("seq");
// seq.model = env.reg_model;  ← model 프로퍼티에 할당
// seq.start(env.apb_agt.sqr);
```

**두 방법 비교:**

| 비교 | p_sequencer 방식 | uvm_reg_sequence 방식 |
|------|-----------------|---------------------|
| **RAL 접근** | `p_sequencer.reg_model` | `model` (내장 프로퍼티) |
| **시퀀서 의존** | 가상 시퀀서 타입에 의존 | 아무 시퀀서에서 실행 가능 |
| **사용 시점** | 가상 시퀀스 (다중 에이전트) | 단일 에이전트 RAL 시퀀스 |
| **설정 방법** | connect_phase에서 자동 | 테스트에서 `seq.model = ...` 수동 할당 |

---

## 13.6 실전 통합: APB + RAL 가상 시퀀스

> **이 절의 목표**: Ch.11~12에서 만든 환경을 가상 시퀀스로 통합하고, 실무 시퀀스 전략을 학습합니다.

### 13.6.1 통합 환경 구성

지금까지 만든 것을 하나로 조합합니다:

```systemverilog
// ============================================================
// 실전 통합 가상 시퀀스: APB 설정 + RAL 검증 + GPIO 제어
// ============================================================
class full_system_virtual_seq extends uvm_sequence;
  `uvm_object_utils(full_system_virtual_seq)
  `uvm_declare_p_sequencer(apb_virtual_sequencer)

  function new(string name = "full_system_virtual_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_reg_block  model;
    uvm_status_e   status;
    uvm_reg_data_t value;

    // 서브 시퀀스
    apb_write_seq     apb_wr;
    gpio_output_seq   gpio_out;

    model = p_sequencer.reg_model;

    `uvm_info(get_type_name(), "========================================", UVM_LOW)
    `uvm_info(get_type_name(), " 실전 통합 시나리오 시작", UVM_LOW)
    `uvm_info(get_type_name(), "========================================", UVM_LOW)

    // ---- Phase 1: RAL로 레지스터 초기화 ----
    `uvm_info(get_type_name(), "[Phase 1] RAL로 레지스터 초기화", UVM_MEDIUM)
    model.ctrl_reg.write(status, 8'h85, .parent(this));   // enable=1, mode=00
    model.data_reg.write(status, 8'hFF, .parent(this));   // data=0xFF

    // ---- Phase 2: GPIO 동시 제어 ----
    `uvm_info(get_type_name(), "[Phase 2] APB + GPIO 동시 동작", UVM_MEDIUM)
    fork
      begin  // APB: 추가 레지스터 쓰기
        apb_wr = apb_write_seq::type_id::create("apb_wr");
        apb_wr.addr = 4'h3;
        apb_wr.data = 8'hBE;
        apb_wr.start(p_sequencer.apb_sqr);
      end
      begin  // GPIO: 출력 제어
        gpio_out = gpio_output_seq::type_id::create("gpio_out");
        gpio_out.out_data = 8'hAA;
        gpio_out.start(p_sequencer.gpio_sqr);
      end
    join

    // ---- Phase 3: RAL로 검증 ----
    `uvm_info(get_type_name(), "[Phase 3] RAL로 레지스터 검증", UVM_MEDIUM)
    model.ctrl_reg.read(status, value, .parent(this));
    `uvm_info(get_type_name(), $sformatf("ctrl_reg = 0x%02h (expected: 0x85)", value), UVM_LOW)

    model.ctrl_reg.mirror(status, UVM_CHECK, .parent(this));
    `uvm_info(get_type_name(), "ctrl_reg mirror 검증 완료", UVM_MEDIUM)

    `uvm_info(get_type_name(), "========================================", UVM_LOW)
    `uvm_info(get_type_name(), " 실전 통합 시나리오 완료", UVM_LOW)
    `uvm_info(get_type_name(), "========================================", UVM_LOW)
  endtask
endclass
```

### 13.6.2 APB + RAL 조합 시나리오

가상 시퀀스의 진정한 가치는 **시나리오 조합**에 있습니다:

```systemverilog
// ============================================================
// 시나리오 조합 예: 스트레스 테스트
// ============================================================
class stress_virtual_seq extends uvm_sequence;
  `uvm_object_utils(stress_virtual_seq)
  `uvm_declare_p_sequencer(apb_virtual_sequencer)

  rand int unsigned num_iterations;
  constraint c_iter { num_iterations inside {[5:20]}; }

  function new(string name = "stress_virtual_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_reg_block  model;
    uvm_status_e   status;
    uvm_reg_data_t value;

    model = p_sequencer.reg_model;

    `uvm_info(get_type_name(), $sformatf("스트레스 테스트: %0d 반복", num_iterations), UVM_LOW)

    repeat(num_iterations) begin
      // 랜덤 레지스터에 랜덤 데이터 쓰기
      bit [7:0] random_data = $urandom;
      bit [3:0] random_addr = $urandom_range(0, 15);

      fork
        begin  // APB 직접 쓰기
          apb_write_seq wr;
          wr = apb_write_seq::type_id::create("wr");
          wr.addr = random_addr;
          wr.data = random_data;
          wr.start(p_sequencer.apb_sqr);
        end
        begin  // GPIO 동시 동작
          gpio_output_seq gpio_out;
          gpio_out = gpio_output_seq::type_id::create("gpio_out");
          gpio_out.start(p_sequencer.gpio_sqr);
        end
      join

      // RAL로 검증 (mirror)
      if (random_addr == 0)
        model.ctrl_reg.mirror(status, UVM_CHECK, .parent(this));
    end

    `uvm_info(get_type_name(), "스트레스 테스트 완료", UVM_LOW)
  endtask
endclass
```

### 13.6.3 Ch.6 기본 시퀀스 vs Ch.13 고급 시퀀스 비교

```
Ch.6 기본 시퀀스 vs Ch.13 고급 시퀀스

┌──────────────────────────────────────────────────────────┐
│             Ch.6 기본 시퀀스          Ch.13 고급 시퀀스  │
│  ┌────────────────────────┐  ┌────────────────────────┐ │
│  │ 제어 대상              │  │ 제어 대상              │ │
│  │ 단일 에이전트          │  │ 다중 에이전트          │ │
│  ├────────────────────────┤  ├────────────────────────┤ │
│  │ 시퀀스 실행            │  │ 시퀀스 실행            │ │
│  │ seq.start(sqr)         │  │ vseq.start(v_sqr)     │ │
│  ├────────────────────────┤  ├────────────────────────┤ │
│  │ 동시성                 │  │ 동시성                 │ │
│  │ 순차 실행만 가능       │  │ fork/join 병렬 실행    │ │
│  ├────────────────────────┤  ├────────────────────────┤ │
│  │ 환경 접근              │  │ 환경 접근              │ │
│  │ 불가 (m_sequencer)     │  │ 가능 (p_sequencer)     │ │
│  ├────────────────────────┤  ├────────────────────────┤ │
│  │ 시나리오 관리          │  │ 시나리오 관리          │ │
│  │ 수동 (코드 하드코딩)   │  │ 자동 (시퀀스 라이브러리)│ │
│  ├────────────────────────┤  ├────────────────────────┤ │
│  │ RAL 연동               │  │ RAL 연동               │ │
│  │ 없음                   │  │ 가상 시퀀스에서 통합   │ │
│  └────────────────────────┘  └────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

| 항목 | Ch.6 기본 시퀀스 | Ch.13 고급 시퀀스 |
|------|-----------------|-------------------|
| **제어 대상** | 단일 에이전트 | 다중 에이전트 |
| **시퀀스 실행** | `seq.start(sqr)` | `vseq.start(v_sqr)` |
| **동시성** | 순차 실행만 | `fork...join` 병렬 실행 |
| **환경 접근** | `m_sequencer` (제한적) | `p_sequencer` (자유로움) |
| **시나리오 관리** | 수동 (코드 하드코딩) | 자동 (시퀀스 라이브러리) |
| **RAL 연동** | 없음 | 가상 시퀀스에서 통합 |
| **사용 시점** | IP 블록 검증 | SoC 통합 검증 |

### 13.6.4 실무 시퀀스 전략 가이드

팹리스 회사에서 시퀀스를 체계적으로 관리하는 전략입니다:

**시퀀스 계층 구조 (실무):**

```
테스트 레벨별 시퀀스 전략

┌─────────────────────────────────────────────┐
│ Level 3: 시스템 시퀀스                       │
│ full_system_seq, stress_seq, corner_case_seq │
│ → 가상 시퀀스 (다중 에이전트 조합)            │
├─────────────────────────────────────────────┤
│ Level 2: 프로토콜 시퀀스                     │
│ apb_burst_seq, apb_error_seq, ral_check_seq  │
│ → 마스터/계층 시퀀스 (단일 에이전트 내)       │
├─────────────────────────────────────────────┤
│ Level 1: 기본 시퀀스                         │
│ apb_write_seq, apb_read_seq, gpio_out_seq    │
│ → 단일 트랜잭션 시퀀스 (빌딩 블록)           │
└─────────────────────────────────────────────┘
```

**시퀀스 네이밍 컨벤션:**

| 레벨 | 접미사 | 예시 |
|------|--------|------|
| Level 1 기본 | `_seq` | `apb_write_seq`, `apb_read_seq` |
| Level 2 프로토콜 | `_scenario_seq` | `apb_init_scenario_seq` |
| Level 3 시스템 | `_virtual_seq` | `full_system_virtual_seq` |
| 라이브러리 | `_lib_seq` | `apb_write_lib_seq` |

**Top 5 시퀀스 실수와 해결법:**

| 순위 | 실수 | 해결법 |
|------|------|--------|
| 1 | 가상 시퀀서 핸들 미할당 (`null`) | `connect_phase`에서 반드시 할당 |
| 2 | `p_sequencer` 선언 누락 | `uvm_declare_p_sequencer` 매크로 추가 |
| 3 | `fork` 안에서 시퀀스 재사용 | `fork` 블록마다 새 시퀀스 `create()` |
| 4 | 시퀀스 라이브러리 `init` 누락 | 생성자에서 `init_sequence_library()` 호출 |
| 5 | RAL `parent` 인자 누락 | `write(status, val, .parent(this))` 명시 |

---

## 13.7 체크포인트

### 13.7.1 셀프 체크

다음 질문에 답할 수 있으면 이 챕터를 이해한 것입니다:

> **Q1**: 가상 시퀀서와 일반 시퀀서의 차이는?
<details>
<summary>정답 보기</summary>
일반 시퀀서는 드라이버와 연결되어 트랜잭션을 전달합니다. 가상 시퀀서는 드라이버와 연결되지 않고, 여러 실제 시퀀서의 **핸들만** 가지고 있는 중앙 허브입니다.
</details>

> **Q2**: 가상 시퀀스에서 하위 시퀀스를 특정 시퀀서에 배포하는 코드는?
<details>
<summary>정답 보기</summary>
`sub_seq.start(p_sequencer.apb_sqr);` — `p_sequencer`를 통해 가상 시퀀서의 실제 시퀀서 핸들에 접근하고, `start()` 인자로 전달합니다.
</details>

> **Q3**: `m_sequencer`와 `p_sequencer`의 차이는?
<details>
<summary>정답 보기</summary>
`m_sequencer`는 `uvm_sequencer_base` 타입으로 모든 시퀀스에 기본 제공됩니다. `p_sequencer`는 `uvm_declare_p_sequencer` 매크로로 선언하며, 사용자 지정 시퀀서 타입으로 캐스팅되어 커스텀 필드(시퀀서 핸들, RAL 모델 등)에 접근할 수 있습니다.
</details>

> **Q4**: 시퀀스 라이브러리의 `UVM_SEQ_LIB_RANDC` 모드는 어떻게 동작하나?
<details>
<summary>정답 보기</summary>
등록된 모든 시퀀스를 **한 번씩** 랜덤 순서로 실행합니다. 모든 시퀀스가 실행된 후 다시 새로운 랜덤 순서로 반복합니다. 특정 시퀀스가 빠지는 일이 없어 커버리지 달성에 유리합니다.
</details>

> **Q5**: 가상 시퀀서의 핸들을 왜 `build_phase`가 아닌 `connect_phase`에서 할당하나?
<details>
<summary>정답 보기</summary>
`build_phase`에서는 하위 컴포넌트의 시퀀서가 아직 생성되지 않았을 수 있습니다. `connect_phase`는 모든 `build_phase`가 완료된 후 실행되므로, 실제 시퀀서가 이미 존재함이 보장됩니다.
</details>

> **Q6**: 가상 시퀀스에서 두 에이전트를 동시에 실행하려면?
<details>
<summary>정답 보기</summary>
`fork...join` 블록 안에서 각 에이전트의 시퀀서에 시퀀스를 `start()`합니다:
```systemverilog
fork
  seq_a.start(p_sequencer.apb_sqr);
  seq_b.start(p_sequencer.gpio_sqr);
join
```
</details>

### 13.7.2 연습문제

**[기본] 연습 1: 가상 시퀀서 확장**

현재 `apb_virtual_sequencer`에 SPI 시퀀서 핸들을 추가하세요. SPI 시퀀스 아이템은 `{mosi_data[7:0], sclk_div[3:0]}` 필드를 가집니다.

<details>
<summary>힌트</summary>

1. `spi_seq_item` 클래스 정의
2. `typedef uvm_sequencer#(spi_seq_item) spi_sequencer;`
3. `apb_virtual_sequencer`에 `spi_sequencer spi_sqr;` 추가
4. 환경의 `connect_phase`에서 핸들 할당
</details>

**[중급] 연습 2: 시퀀스 라이브러리에 에러 시퀀스 추가**

`apb_seq_library`에 잘못된 주소(0xF 이상)로 접근하는 에러 시퀀스를 추가하세요. `uvm_add_to_seq_lib` 매크로를 사용합니다.

<details>
<summary>힌트</summary>

```systemverilog
class apb_error_lib_seq extends uvm_sequence#(apb_seq_item);
  `uvm_object_utils(apb_error_lib_seq)
  `uvm_add_to_seq_lib(apb_error_lib_seq, apb_seq_library)
  // paddr에 범위 밖 주소를 설정
endclass
```
</details>

**[고급] 연습 3: RAL + 가상 시퀀스 조합**

다음 시나리오를 가상 시퀀스로 구현하세요:
1. RAL로 `ctrl_reg`에 `enable=1, mode=01` 설정
2. GPIO로 데이터 출력 (동시 실행)
3. RAL로 `status_reg` 읽고 `mirror()` 검증
4. 모든 레지스터에 대해 `uvm_reg_hw_reset_seq` 실행

<details>
<summary>힌트</summary>

```systemverilog
class advanced_virtual_seq extends uvm_sequence;
  `uvm_declare_p_sequencer(apb_virtual_sequencer)

  virtual task body();
    apb_reg_block model = p_sequencer.reg_model;
    // Phase 1: model.ctrl_reg.write(...)
    // Phase 2: fork...join (GPIO + APB)
    // Phase 3: model.status_reg.mirror(...)
    // Phase 4: uvm_reg_hw_reset_seq reset_seq;
    //          reset_seq.model = model;
    //          reset_seq.start(p_sequencer.apb_sqr);
  endtask
endclass
```
</details>

### 13.7.3 이 챕터에서 배운 것

이 챕터에서 추가한 고급 시퀀스 관련 파일:

```
apb_verification/
├── rtl/
│   └── apb_slave_memory.sv    ← Ch.11 (변경 없음)
├── tb/
│   ├── apb_if.sv              ← Ch.11 (변경 없음)
│   ├── apb_seq_item.sv        ← Ch.11 (변경 없음)
│   ├── apb_driver.sv          ← Ch.11 (변경 없음)
│   ├── apb_monitor.sv         ← Ch.11 (변경 없음)
│   ├── apb_agent.sv           ← Ch.11 (변경 없음)
│   ├── apb_reg_classes.sv     ← Ch.12 (변경 없음)
│   ├── apb_reg_block.sv       ← Ch.12 (변경 없음)
│   ├── apb_reg_adapter.sv     ← Ch.12 (변경 없음)
│   ├── apb_ral_env.sv         ← Ch.12 (변경 없음)
│   ├── gpio_seq_item.sv       ← NEW: GPIO 시퀀스 아이템
│   ├── apb_virtual_sequencer.sv  ← NEW: 가상 시퀀서
│   ├── apb_virtual_env.sv     ← NEW: 가상 시퀀서 포함 환경
│   ├── apb_gpio_virtual_seq.sv   ← NEW: 가상 시퀀스
│   ├── apb_seq_library.sv     ← NEW: 시퀀스 라이브러리
│   └── apb_virtual_test.sv    ← NEW: 가상 시퀀스 테스트
└── sim/
    └── run.do
```

Ch.11~12의 코드는 **한 줄도 변경하지 않았습니다.** 가상 시퀀서와 가상 시퀀스는 기존 에이전트 위에 **제어 계층을 추가**하는 것입니다. 이것이 UVM의 계층적 설계 철학입니다.

### 13.7.4 다음 장 미리보기

Chapter 14에서는 **검증 자동화**를 배웁니다. 커버리지(Coverage) 수집으로 "검증을 얼마나 했는지" 측정하고, 어서션(Assertion)으로 프로토콜 규칙을 자동 검사합니다. Ch.11~13에서 만든 APB 검증 환경에 커버리지와 어서션을 추가하여 **완전한 검증 인프라**를 구축합니다.

**Part 3 진행 현황:**

| 챕터 | 주제 | 핵심 | 상태 |
|------|------|------|------|
| **Ch.11** | 인터페이스와 BFM | APB 에이전트 구축 | ✅ 완료 |
| **Ch.12** | 레지스터 모델 (RAL) | APB 위에 RAL 계층 추가 | ✅ 완료 |
| **Ch.13** | 고급 시퀀스 | 가상 시퀀스, 시퀀스 라이브러리 | ✅ 지금 여기! |
| **Ch.14** | 검증 자동화 | 커버리지, 어서션 | 다음 |
| **Ch.15** | 프로젝트 종합 | 전체 통합 및 리뷰 | 대기 |

> 💡 **핵심 메시지**: Ch.6에서 "하나의 시퀀서에 하나의 시퀀스"를 배웠다면, Ch.13에서는 "여러 시퀀서를 하나의 악보로 지휘"하는 법을 배웠습니다. 가상 시퀀스는 SoC 레벨 검증의 **필수 도구**입니다. Ch.14에서는 이 환경에 커버리지와 어서션을 추가하여 "검증이 충분한지"를 측정합니다.
