# Chapter 12: 레지스터 모델 (RAL)

> **이 챕터의 목표**: Ch.11에서 구축한 APB 에이전트 위에 **UVM RAL(Register Abstraction Layer)**을 올려, 레지스터의 필드별 접근, 자동 읽기/쓰기 테스트, 백도어 접근을 구현합니다. 수동 검증에서 자동화된 레지스터 검증으로 전환하는 과정을 체험합니다.

> **선수 지식**: Chapter 11 (APB 인터페이스와 BFM), Chapter 8 (스코어보드와 analysis port), Chapter 6 (시퀀스)

---

## 12.1 왜 레지스터 모델이 필요한가

> **이 절의 목표**: Ch.11에서 수동으로 수행한 레지스터 검증의 한계를 인식하고, RAL의 필요성과 아키텍처를 이해합니다.

### 12.1.1 Ch.11 방식의 한계 — 수동 검증

Ch.11에서 APB Slave Memory의 16개 레지스터를 검증할 때, 이렇게 했습니다:

```systemverilog
// Ch.11 방식: 수동으로 주소/데이터 지정
wr_seq.target_addr = 4'h3;    // 주소 0x3
wr_seq.target_data = 8'hAB;   // 데이터 0xAB
wr_seq.start(m_sequencer);

rd_seq.target_addr = 4'h3;
rd_seq.start(m_sequencer);
// 결과 비교도 수동
if (rd_seq.read_data !== 8'hAB) `uvm_error(...)
```

이 방식은 동작하지만, 실무에서는 한계가 있습니다:

| 문제 | 설명 |
|------|------|
| **확장성** | SoC에는 수백~수천 개 레지스터가 있음. 각각 수동으로 주소/값 지정? |
| **필드 접근** | 8비트 레지스터 내 개별 비트 필드를 다루려면 마스킹 연산 필요 |
| **자동 테스트** | "모든 레지스터가 리셋 값이 맞는가?" 같은 검증을 일일이 코딩? |
| **문서 동기화** | 레지스터 사양(스펙)이 바뀌면 테스트 코드를 전부 수정 |
| **재사용** | 다른 프로젝트에서 같은 IP를 사용하면 처음부터 다시 작성 |

> 💡 **실무 상황**: 팹리스 회사에서 SoC 하나에 레지스터가 3,000개 이상인 경우가 흔합니다. 이것을 수동으로 검증하는 것은 사실상 불가능합니다.

### 12.1.2 RAL이란? — 레지스터 추상화 계층

**UVM RAL(Register Abstraction Layer)**은 DUT의 레지스터를 **소프트웨어 객체로 모델링**하는 프레임워크입니다.

**핵심 아이디어:**

```
전통적 방법:                    RAL 방법:
시퀀스에서 직접 주소 지정       시퀀스에서 레지스터 이름으로 접근
  addr = 4'h3;                   reg_model.ctrl_reg.write(status, 8'hAB);
  data = 8'hAB;                  reg_model.ctrl_reg.read(status, rdata);
  write(addr, data);
```

**RAL의 가치:**

1. **추상화**: 주소 대신 **이름**으로 접근 (`ctrl_reg.enable.set(1)`)
2. **자동 테스트**: 내장 시퀀스로 리셋 값, 비트 접근 등을 자동 검증
3. **미러링**: RAL이 DUT의 레지스터 상태를 **자동 추적** (desired/mirrored 값)
4. **재사용**: 레지스터 모델만 교체하면 다른 IP에도 적용 가능
5. **문서 연동**: 레지스터 사양에서 RAL 코드를 **자동 생성** 가능 (ralgen, IDesignSpec 등)

### 12.1.3 RAL 아키텍처

```
┌───────────────────────────────────────────────────────────────┐
│                    RAL 아키텍처 개요                            │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│   테스트/시퀀스                                                │
│       │                                                       │
│       ▼                                                       │
│   ┌─────────────────────────────────────────┐                │
│   │         Register Model (uvm_reg_block)   │                │
│   │  ┌──────────┐  ┌──────────┐             │                │
│   │  │ ctrl_reg  │  │ data_reg  │  ...       │                │
│   │  │ ┌──────┐ │  │ ┌──────┐ │             │                │
│   │  │ │field │ │  │ │field │ │             │                │
│   │  │ └──────┘ │  │ └──────┘ │             │                │
│   │  └──────────┘  └──────────┘             │                │
│   │         uvm_reg_map (주소 매핑)          │                │
│   └─────────────────┬───────────────────────┘                │
│                     │                                         │
│                     ▼                                         │
│   ┌────────────────────────────┐                              │
│   │  Adapter (reg2bus/bus2reg)  │                              │
│   └────────────┬───────────────┘                              │
│                │                                               │
│                ▼                                               │
│   ┌────────────────────────────┐  ┌────────────────────────┐ │
│   │    APB Agent (Sequencer)    │  │  Predictor (auto-mirror)│ │
│   │    Driver ──→ DUT           │  │  Monitor ──→ Predictor  │ │
│   └────────────────────────────┘  └────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**흐름:**
1. 테스트/시퀀스가 RAL 모델에게 `write()`/`read()` 요청
2. RAL 모델이 **Adapter**를 통해 APB 트랜잭션으로 변환
3. APB 에이전트의 시퀀서 → 드라이버가 실제 버스에 전송
4. **Predictor**가 모니터의 관찰 결과로 RAL 미러 값을 자동 업데이트

> 💡 **비유**: RAL은 "은행 ATM"과 같습니다. ATM(RAL)에서 "이체"라고 누르면, 내부적으로 은행 전산망(APB 버스)을 통해 실제 계좌(DUT 레지스터)에 접근합니다. 사용자는 전산망의 프로토콜을 알 필요 없이 이름과 금액만 입력하면 됩니다.

---

## 12.2 RAL 구성 요소

> **이 절의 목표**: RAL을 이루는 4가지 핵심 클래스(uvm_reg_field, uvm_reg, uvm_reg_block, uvm_reg_map)를 이해합니다.

### 12.2.1 uvm_reg_field — 비트 필드 정의

레지스터 안의 **개별 비트 그룹**을 표현합니다:

```systemverilog
// ──────────────────────────────────────────
// 예시: 8비트 Control 레지스터의 필드 구성
// [7]    = enable (R/W, 리셋값 0)
// [6:5]  = mode   (R/W, 리셋값 0)
// [4:0]  = reserved (R/O, 리셋값 0)
// ──────────────────────────────────────────
```

`uvm_reg_field`의 `configure()` 메서드:

```systemverilog
field.configure(
  .parent     (this),         // 소속 레지스터
  .size       (1),            // 비트 수
  .lsb_pos    (7),            // 시작 비트 위치
  .access     ("RW"),         // 접근 타입
  .volatile   (0),            // 하드웨어가 자체 변경하는가?
  .reset      (1'b0),         // 리셋 값
  .has_reset  (1),            // 리셋 값이 있는가?
  .is_rand    (1),            // 랜덤화 가능?
  .individually_accessible(0) // 개별 접근 가능?
);
```

**주요 접근 타입:**

| 타입 | 의미 | 예시 |
|------|------|------|
| `"RW"` | 읽기/쓰기 | 일반 설정 레지스터 |
| `"RO"` | 읽기 전용 | 상태 레지스터, 버전 정보 |
| `"WO"` | 쓰기 전용 | 명령 트리거 |
| `"W1C"` | 1을 쓰면 클리어 | 인터럽트 상태 |
| `"RC"` | 읽으면 클리어 | FIFO 카운터 |

### 12.2.2 uvm_reg — 레지스터 정의

하나의 **레지스터**를 표현합니다. 여러 `uvm_reg_field`를 포함:

```systemverilog
// ──────────────────────────────────────────
// Control 레지스터 정의
// 파일: apb_ctrl_reg.sv
// 주소: 0x0, 8비트, 3개 필드
// ──────────────────────────────────────────
class apb_ctrl_reg extends uvm_reg;
  `uvm_object_utils(apb_ctrl_reg)

  // 필드 선언
  rand uvm_reg_field enable;    // [7]    R/W
  rand uvm_reg_field mode;      // [6:5]  R/W
  rand uvm_reg_field reserved;  // [4:0]  R/O

  function new(string name = "apb_ctrl_reg");
    // 8비트 레지스터, 커버리지 없음
    super.new(name, 8, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    // ── 필드 생성 및 설정 ──
    enable = uvm_reg_field::type_id::create("enable");
    enable.configure(this, 1, 7, "RW", 0, 1'b0, 1, 1, 0);
    //                      size=1, lsb=7, RW, reset=0

    mode = uvm_reg_field::type_id::create("mode");
    mode.configure(this, 2, 5, "RW", 0, 2'b00, 1, 1, 0);
    //                    size=2, lsb=5, RW, reset=0

    reserved = uvm_reg_field::type_id::create("reserved");
    reserved.configure(this, 5, 0, "RO", 0, 5'b0, 1, 0, 0);
    //                       size=5, lsb=0, RO, reset=0, rand=0
  endfunction
endclass
```

**핵심 포인트:**
- `super.new(name, 8, UVM_NO_COVERAGE)` — 8비트 레지스터
- `build()` 함수에서 필드를 생성하고 `configure()`로 속성 설정
- 필드들의 비트 위치가 겹치지 않아야 합니다 (enable=7, mode=6:5, reserved=4:0)

### 12.2.3 uvm_reg_block과 uvm_reg_map — 주소 매핑

**`uvm_reg_block`**은 여러 레지스터를 그룹으로 묶고, **`uvm_reg_map`**은 각 레지스터의 주소를 매핑합니다:

```systemverilog
// ──────────────────────────────────────────
// 레지스터 블록 (간단한 예시)
// ──────────────────────────────────────────
class apb_reg_block extends uvm_reg_block;
  `uvm_object_utils(apb_reg_block)

  // 레지스터 선언
  rand apb_ctrl_reg ctrl_reg;    // 주소 0x0
  rand apb_data_reg data_reg;    // 주소 0x1

  // 레지스터 맵
  uvm_reg_map reg_map;

  function new(string name = "apb_reg_block");
    super.new(name, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    // 레지스터 생성
    ctrl_reg = apb_ctrl_reg::type_id::create("ctrl_reg");
    ctrl_reg.configure(this);  // 이 블록에 소속
    ctrl_reg.build();          // 필드 생성

    data_reg = apb_data_reg::type_id::create("data_reg");
    data_reg.configure(this);
    data_reg.build();

    // 레지스터 맵 생성 — 주소 매핑
    reg_map = create_map(
      "reg_map",    // 맵 이름
      'h0,          // 베이스 주소
      1,            // 주소 단위 (바이트)
      UVM_LITTLE_ENDIAN  // 엔디안
    );

    // 레지스터를 맵에 추가 (주소 할당)
    reg_map.add_reg(ctrl_reg, 'h0, "RW");  // 주소 0x0
    reg_map.add_reg(data_reg, 'h1, "RW");  // 주소 0x1
  endfunction
endclass
```

**핵심:**
- `create_map()` — 주소 공간 정의 (베이스 주소, 바이트 단위, 엔디안)
- `add_reg()` — 레지스터에 오프셋 주소 할당
- 하나의 레지스터 블록에 여러 맵을 가질 수 있습니다 (APB맵, AXI맵 등)

### 12.2.4 계층 구조 요약

```
┌─────────────────────────────────────────────────────┐
│             RAL 계층 구조                             │
├─────────────────────────────────────────────────────┤
│                                                       │
│   uvm_reg_block (레지스터 블록)                       │
│   ├── uvm_reg_map (주소 매핑)                        │
│   │     addr 0x0 → ctrl_reg                          │
│   │     addr 0x1 → data_reg                          │
│   │     addr 0x2 → status_reg                        │
│   │     ...                                          │
│   │                                                   │
│   ├── uvm_reg (레지스터)                              │
│   │   ├── uvm_reg_field (enable)  [7]    RW          │
│   │   ├── uvm_reg_field (mode)    [6:5]  RW          │
│   │   └── uvm_reg_field (reserved)[4:0]  RO          │
│   │                                                   │
│   └── uvm_reg (또 다른 레지스터)                      │
│       ├── uvm_reg_field (...)                         │
│       └── uvm_reg_field (...)                         │
│                                                       │
└─────────────────────────────────────────────────────┘
```

**기억할 관계:**
- **Block** → 1개 이상의 **Map** + 여러 **Reg**
- **Map** → 각 Reg에 주소 할당
- **Reg** → 1개 이상의 **Field**
- **Field** → 비트 위치, 접근 타입, 리셋 값

---

## 12.3 APB Slave Memory 레지스터 모델

> **이 절의 목표**: Ch.11의 APB Slave Memory DUT에 대한 완전한 레지스터 모델을 구현합니다.

### 12.3.1 레지스터 사양 정의

Ch.11의 DUT는 16개의 8비트 레지스터를 가집니다. RAL을 의미있게 활용하기 위해, 각 레지스터에 필드 의미를 부여합니다:

| 주소 | 이름 | 필드 | 접근 | 리셋 값 | 설명 |
|------|------|------|------|---------|------|
| 0x0 | `ctrl_reg` | enable[7], mode[6:5], rsv[4:0] | RW/RW/RO | 0x00 | 제어 레지스터 |

**ctrl_reg 비트 필드 맵:**

```
┌──────────────────────────────────────────────┐
│            ctrl_reg (8비트, 주소 0x0)          │
├────┬────────┬────────────────────────────────┤
│ 비트│  7     │  6     5  │  4  3  2  1  0   │
├────┼────────┼────────────┼──────────────────┤
│필드│ enable │   mode     │    reserved       │
│접근│  R/W   │   R/W      │      R/O          │
│리셋│   0    │   00       │     00000         │
└────┴────────┴────────────┴──────────────────┘
```


| 0x1 | `status_reg` | busy[7], error[6], rsv[5:0] | RO/RO/RO | 0x00 | 상태 레지스터 |
| 0x2 | `data_reg` | data[7:0] | RW | 0x00 | 데이터 레지스터 |
| 0x3~0xF | `gp_reg[0:12]` | data[7:0] | RW | 0x00 | 범용 레지스터 |

> 💡 **실무 참고**: 실제 프로젝트에서는 레지스터 사양 문서(Register Specification)를 먼저 작성하고, 이로부터 RAL 코드를 자동 생성합니다. 여기서는 학습을 위해 수동으로 작성합니다.

### 12.3.2 레지스터 클래스 구현

```systemverilog
// ──────────────────────────────────────────
// APB Slave Memory — 레지스터 정의
// 파일: apb_reg_classes.sv
// 역할: 각 레지스터의 필드 구조를 RAL로 모델링
// ──────────────────────────────────────────

// ── Control 레지스터 (주소 0x0) ──
class apb_ctrl_reg extends uvm_reg;
  `uvm_object_utils(apb_ctrl_reg)

  rand uvm_reg_field enable;    // [7]    — 동작 활성화
  rand uvm_reg_field mode;      // [6:5]  — 동작 모드 선택
       uvm_reg_field reserved;  // [4:0]  — 예약 (RO)

  function new(string name = "apb_ctrl_reg");
    super.new(name, 8, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    enable = uvm_reg_field::type_id::create("enable");
    enable.configure(this, 1, 7, "RW", 0, 1'b0, 1, 1, 0);

    mode = uvm_reg_field::type_id::create("mode");
    mode.configure(this, 2, 5, "RW", 0, 2'b00, 1, 1, 0);

    reserved = uvm_reg_field::type_id::create("reserved");
    reserved.configure(this, 5, 0, "RO", 0, 5'b0, 1, 0, 0);
  endfunction
endclass

// ── Status 레지스터 (주소 0x1) ──
class apb_status_reg extends uvm_reg;
  `uvm_object_utils(apb_status_reg)

  uvm_reg_field busy;      // [7]    — 처리 중 플래그
  uvm_reg_field error;     // [6]    — 에러 플래그
  uvm_reg_field reserved;  // [5:0]  — 예약

  function new(string name = "apb_status_reg");
    super.new(name, 8, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    busy = uvm_reg_field::type_id::create("busy");
    busy.configure(this, 1, 7, "RO", 1, 1'b0, 1, 0, 0);
    //                              volatile=1 (HW가 변경)

    error = uvm_reg_field::type_id::create("error");
    error.configure(this, 1, 6, "RO", 1, 1'b0, 1, 0, 0);

    reserved = uvm_reg_field::type_id::create("reserved");
    reserved.configure(this, 6, 0, "RO", 0, 6'b0, 1, 0, 0);
  endfunction
endclass

// ── Data/범용 레지스터 (주소 0x2~0xF) ──
class apb_data_reg extends uvm_reg;
  `uvm_object_utils(apb_data_reg)

  rand uvm_reg_field data;  // [7:0] — 전체 8비트 데이터

  function new(string name = "apb_data_reg");
    super.new(name, 8, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    data = uvm_reg_field::type_id::create("data");
    data.configure(this, 8, 0, "RW", 0, 8'h0, 1, 1, 0);
  endfunction
endclass
```

### 12.3.3 레지스터 블록 구현

```systemverilog
// ──────────────────────────────────────────
// APB Slave Memory — 레지스터 블록
// 파일: apb_reg_block.sv
// 역할: 16개 레지스터를 하나의 블록으로 묶고 주소 매핑
// ──────────────────────────────────────────
class apb_slave_reg_block extends uvm_reg_block;
  `uvm_object_utils(apb_slave_reg_block)

  // ── 레지스터 선언 ──
  rand apb_ctrl_reg   ctrl_reg;       // 주소 0x0
  rand apb_status_reg status_reg;     // 주소 0x1
  rand apb_data_reg   data_reg;       // 주소 0x2
  rand apb_data_reg   gp_reg[13];     // 주소 0x3~0xF (13개 범용)

  uvm_reg_map reg_map;

  function new(string name = "apb_slave_reg_block");
    super.new(name, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    // ── 레지스터 생성 ──
    ctrl_reg = apb_ctrl_reg::type_id::create("ctrl_reg");
    ctrl_reg.configure(this);
    ctrl_reg.build();

    status_reg = apb_status_reg::type_id::create("status_reg");
    status_reg.configure(this);
    status_reg.build();

    data_reg = apb_data_reg::type_id::create("data_reg");
    data_reg.configure(this);
    data_reg.build();

    foreach (gp_reg[i]) begin
      gp_reg[i] = apb_data_reg::type_id::create($sformatf("gp_reg_%0d", i));
      gp_reg[i].configure(this);
      gp_reg[i].build();
    end

    // ── 레지스터 맵 생성 ──
    reg_map = create_map("reg_map", 'h0, 1, UVM_LITTLE_ENDIAN);

    // 주소 매핑
    reg_map.add_reg(ctrl_reg,   'h0, "RW");
    reg_map.add_reg(status_reg, 'h1, "RO");
    reg_map.add_reg(data_reg,   'h2, "RW");
    foreach (gp_reg[i])
      reg_map.add_reg(gp_reg[i], 'h3 + i, "RW");

    // 맵 잠금 — 빌드 완료 후 반드시 호출
    lock_model();
  endfunction
endclass
```

**핵심 포인트:**
- `foreach (gp_reg[i])` — 13개 범용 레지스터를 루프로 생성
- `lock_model()` — 레지스터 모델의 빌드가 완료되었음을 선언. **빠뜨리면 런타임 에러** 발생
- `create_map("reg_map", 'h0, 1, UVM_LITTLE_ENDIAN)` — 바이트 단위 주소, 리틀 엔디안

> ⚠️ **초보자 주의**: `lock_model()`을 빠뜨리는 것은 가장 흔한 RAL 실수입니다. 이를 호출하지 않으면 `UVM_FATAL: "Register model has not been locked!"` 에러가 발생합니다.

---

## 12.4 RAL과 APB 에이전트 연결

> **이 절의 목표**: Adapter와 Predictor를 구현하여 RAL 모델과 Ch.11의 APB 에이전트를 연결합니다.

### 12.4.1 Adapter — 트랜잭션 변환기

**Adapter**는 RAL의 일반적인 레지스터 읽기/쓰기 요청을 **APB 트랜잭션**으로 변환하는 "번역기"입니다.

```systemverilog
// ──────────────────────────────────────────
// APB RAL Adapter
// 파일: apb_reg_adapter.sv
// 역할: RAL ↔ APB 트랜잭션 변환
// ──────────────────────────────────────────
class apb_reg_adapter extends uvm_reg_adapter;
  `uvm_object_utils(apb_reg_adapter)

  function new(string name = "apb_reg_adapter");
    super.new(name);

    // ── 중요 설정 ──
    // RAL이 시퀀서를 통해 아이템을 전송하도록 설정
    supports_byte_enable = 0;
    provides_responses   = 0;
  endfunction

  // ── RAL → APB 변환 (reg2bus) ──
  // RAL이 write()/read()를 호출하면 이 함수가 호출됨
  virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);
    apb_seq_item item = apb_seq_item::type_id::create("item");

    item.write = (rw.kind == UVM_WRITE);
    item.addr  = rw.addr[3:0];
    item.wdata = rw.data[7:0];

    `uvm_info(get_type_name(),
      $sformatf("reg2bus: %s addr=0x%0h data=0x%0h",
                (rw.kind == UVM_WRITE) ? "WRITE" : "READ",
                rw.addr, rw.data), UVM_HIGH)

    return item;
  endfunction

  // ── APB → RAL 변환 (bus2reg) ──
  // APB 트랜잭션 완료 후 RAL에 결과를 전달
  virtual function void bus2reg(uvm_sequence_item bus_item,
                                ref uvm_reg_bus_op rw);
    apb_seq_item item;

    if (!$cast(item, bus_item)) begin
      `uvm_fatal(get_type_name(), "bus2reg: 타입 변환 실패")
      return;
    end

    rw.kind   = item.write ? UVM_WRITE : UVM_READ;
    rw.addr   = item.addr;
    rw.data   = item.write ? item.wdata : item.rdata;
    rw.status = UVM_IS_OK;

    `uvm_info(get_type_name(),
      $sformatf("bus2reg: %s addr=0x%0h data=0x%0h",
                (rw.kind == UVM_WRITE) ? "WRITE" : "READ",
                rw.addr, rw.data), UVM_HIGH)
  endfunction
endclass
```

**핵심:**
- `reg2bus()` — RAL의 추상적 읽기/쓰기 → APB 트랜잭션 (apb_seq_item) 생성
- `bus2reg()` — APB 트랜잭션 완료 → RAL에 결과 전달 (rdata 등)
- `supports_byte_enable = 0` — APB는 바이트 이네이블 불필요
- `provides_responses = 0` — 별도 응답 시퀀스 없음

> 💡 **비유**: Adapter는 "통역사"입니다. RAL이 한국어로 "주소 3번에 0xAB 써줘"라고 하면, Adapter가 APB 프로토콜의 언어(apb_seq_item)로 번역해서 APB 에이전트에 전달합니다.

### 12.4.2 Predictor — 자동 미러링

**Predictor**는 모니터가 관찰한 APB 트랜잭션을 RAL 모델에 자동으로 반영하여 **미러 값**을 최신 상태로 유지합니다.

> 💡 **비유**: Predictor는 "은행 앱의 자동 잔고 업데이트"와 같습니다. ATM(Adapter)에서 돈을 인출하면, 은행 앱(Predictor)이 거래 내역(모니터 관찰)을 감지하여 잔고(mirrored 값)를 자동으로 갱신합니다. 사용자가 직접 잔고를 계산할 필요가 없습니다.

```systemverilog
// Predictor는 UVM 내장 클래스를 그대로 사용합니다:
// uvm_reg_predictor #(apb_seq_item)
```

Predictor 설정은 환경에서 합니다 (12.4.3 참조).

**desired / mirrored / actual 값의 의미:**

| 값 | 위치 | 의미 | 업데이트 시점 |
|------|------|------|-------------|
| **desired** | RAL 모델 | "이 값을 쓰고 싶다" | `set()` 호출 시 |
| **mirrored** | RAL 모델 | "DUT에 이 값이 있을 것이다" | `write()`/`read()` 완료 시 |
| **actual** | DUT 하드웨어 | 실제 레지스터 값 | 하드웨어 동작 시 |

```
예시: ctrl_reg.enable에 1을 쓰는 과정

   set(1)          write()           DUT 반영
desired: 0→1    mirrored: 0→1    actual: 0→1
    │               │                │
    ▼               ▼                ▼
   RAL 모델      RAL + Adapter     하드웨어
```

> 💡 **핵심**: `mirrored` 값은 RAL이 **추정하는** DUT 값입니다. Predictor가 모니터 관찰 결과로 이를 업데이트하므로, 항상 DUT 실제 값과 동기화됩니다 (하드웨어가 자체 변경하는 volatile 필드 제외).

### 12.4.3 환경에 RAL 통합

```systemverilog
// ──────────────────────────────────────────
// RAL 통합 환경
// 파일: apb_ral_env.sv
// 역할: Ch.11의 apb_env에 RAL 모델, Adapter, Predictor 추가
// ──────────────────────────────────────────
class apb_ral_env extends uvm_env;
  `uvm_component_utils(apb_ral_env)

  // Ch.11에서 만든 APB 에이전트
  apb_agent agent;

  // RAL 구성 요소
  apb_slave_reg_block  reg_model;   // 레지스터 모델
  apb_reg_adapter      adapter;     // 트랜잭션 변환기
  uvm_reg_predictor #(apb_seq_item) predictor;  // 자동 미러링

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // ── APB 에이전트 생성 (Ch.11과 동일) ──
    agent = apb_agent::type_id::create("agent", this);

    // ── RAL 모델 생성 ──
    reg_model = apb_slave_reg_block::type_id::create("reg_model");
    reg_model.build();   // 레지스터 + 맵 생성
    // lock_model()은 build() 안에서 호출됨

    // ── Adapter 생성 ──
    adapter = apb_reg_adapter::type_id::create("adapter");

    // ── Predictor 생성 ──
    predictor = uvm_reg_predictor#(apb_seq_item)::type_id::create(
      "predictor", this);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);

    // ── 핵심 연결 0: auto_predict 비활성화 ──
    // Predictor를 사용하므로 자동 예측을 끔
    // (기본값은 auto_predict=1이며, Predictor와 중복되어 오동작 가능)
    reg_model.reg_map.set_auto_predict(0);

    // ── 핵심 연결 1: 레지스터 맵 → 시퀀서 + Adapter ──
    // RAL이 APB 시퀀서를 통해 트랜잭션을 전송하도록 설정
    reg_model.reg_map.set_sequencer(
      agent.sequencer, adapter);

    // ── 핵심 연결 2: Predictor 설정 ──
    predictor.map     = reg_model.reg_map;
    predictor.adapter = adapter;

    // ── 핵심 연결 3: 모니터 → Predictor ──
    // 모니터가 관찰한 트랜잭션을 Predictor에 전달
    agent.monitor.ap.connect(predictor.bus_in);
  endfunction
endclass
```

**4개의 핵심 연결:**

0. **`set_auto_predict(0)`** — Predictor 사용 시 자동 예측 비활성화 (중복 방지)
1. **`set_sequencer(sequencer, adapter)`** — RAL → Adapter → APB 시퀀서 경로
2. **`predictor.map = reg_map`** — Predictor가 어떤 맵을 업데이트할지 지정
3. **`monitor.ap.connect(predictor.bus_in)`** — 모니터 관찰 → Predictor → RAL 미러 업데이트

> ⚠️ **초보자 주의**: `set_auto_predict(0)`을 빠뜨리면, RAL이 자체적으로 미러 값을 업데이트하면서 동시에 Predictor도 업데이트하여 **이중 업데이트** 문제가 발생합니다. Predictor를 사용할 때는 반드시 `set_auto_predict(0)`을 설정하세요.

> ⚠️ **초보자 주의**: 이 4개 연결 중 하나라도 빠지면 RAL이 정상 동작하지 않습니다. 특히 `set_sequencer()`를 빠뜨리면 `UVM_FATAL: "No sequencer registered..."` 에러가 발생합니다.

**RAL 통합 체크리스트:**

RAL 환경 설정 시 빠뜨리기 쉬운 항목들을 정리합니다:

| 단계 | 코드 | 위치 | 빠뜨리면? |
|------|------|------|----------|
| 1 | `reg_model.build()` | `build_phase` | 레지스터 없음 |
| 2 | `lock_model()` | `build()` 내부 | FATAL 에러 |
| 3 | `set_auto_predict(0)` | `connect_phase` | 미러 이중 업데이트 |
| 4 | `set_sequencer(sqr, adapter)` | `connect_phase` | FATAL 에러 |
| 5 | `predictor.map = reg_map` | `connect_phase` | Predictor 미동작 |
| 6 | `predictor.adapter = adapter` | `connect_phase` | 변환 실패 |
| 7 | `monitor.ap.connect(predictor.bus_in)` | `connect_phase` | 미러 미갱신 |

이 7단계를 순서대로 확인하면 RAL 통합의 대부분의 문제를 예방할 수 있습니다.

---

## 12.5 RAL 기본 동작

> **이 절의 목표**: RAL을 통해 레지스터를 읽고 쓰는 기본 동작을 실습합니다.

### 12.5.1 Frontdoor 읽기/쓰기

RAL의 기본 접근 방식은 **Frontdoor** — 실제 버스(APB)를 통해 DUT에 접근합니다:

```systemverilog
// ── RAL을 통한 레지스터 접근 ──
uvm_status_e status;
uvm_reg_data_t rdata;

// [방법 1] write() — 전체 레지스터 쓰기
reg_model.ctrl_reg.write(status, 8'h80);
// → Adapter가 APB WRITE(addr=0x0, data=0x80)으로 변환
// → APB 드라이버가 실제 버스에 전송

// [방법 2] read() — 전체 레지스터 읽기
reg_model.ctrl_reg.read(status, rdata);
// → Adapter가 APB READ(addr=0x0)으로 변환
// → 결과가 rdata에 저장

// [방법 3] 필드 레벨 접근 — set() + update()
reg_model.ctrl_reg.enable.set(1);    // desired 값 설정
reg_model.ctrl_reg.mode.set(2'b11);  // desired 값 설정
reg_model.ctrl_reg.update(status);   // 변경된 필드만 버스에 반영
// → enable=1, mode=11 → 0xE0 = {1, 11, 00000}

// [방법 4] mirror() — DUT 값을 읽어서 mirrored 업데이트
reg_model.ctrl_reg.mirror(status, UVM_CHECK);
// UVM_CHECK: 읽은 값과 mirrored 값을 비교 (불일치 시 에러)
// UVM_NO_CHECK: 비교 없이 mirrored만 업데이트
```

**Ch.11 방식과 비교:**

| 동작 | Ch.11 (수동) | Ch.12 (RAL) |
|------|-------------|-------------|
| Write 0x80 to addr 0 | `wr_seq.target_addr=0; wr_seq.target_data=8'h80;` | `reg_model.ctrl_reg.write(status, 8'h80);` |
| Read from addr 0 | `rd_seq.target_addr=0; rd_seq.start(...)` | `reg_model.ctrl_reg.read(status, rdata);` |
| Enable 비트만 1로 | `wr_seq.target_data=8'h80; // 수동 계산` | `reg_model.ctrl_reg.enable.set(1);` |
| 리셋 값 확인 | 16개 주소 일일이 읽기 | `uvm_reg_hw_reset_seq` 1줄 |

### 12.5.2 RAL 시퀀스 작성

```systemverilog
// ──────────────────────────────────────────
// RAL 기반 레지스터 테스트 시퀀스
// 파일: apb_ral_test_seq.sv
// 역할: RAL을 통해 레지스터 읽기/쓰기/필드 접근 시연
// ──────────────────────────────────────────
class apb_ral_test_seq extends uvm_reg_sequence;
  `uvm_object_utils(apb_ral_test_seq)

  apb_slave_reg_block reg_model;

  function new(string name = "apb_ral_test_seq");
    super.new(name);
  endfunction

  task body();
    uvm_status_e status;
    uvm_reg_data_t rdata;

    `uvm_info(get_type_name(),
      "=== RAL 레지스터 테스트 시작 ===", UVM_NONE)

    // ── 테스트 1: 전체 레지스터 Write/Read ──
    `uvm_info(get_type_name(), "--- 테스트 1: Write/Read ---", UVM_LOW)

    // ctrl_reg에 0xA0 쓰기 (enable=1, mode=01, rsv=0)
    reg_model.ctrl_reg.write(status, 8'hA0);
    if (status != UVM_IS_OK)
      `uvm_error(get_type_name(), "ctrl_reg write 실패")

    // ctrl_reg 읽기
    reg_model.ctrl_reg.read(status, rdata);
    `uvm_info(get_type_name(),
      $sformatf("ctrl_reg read: 0x%0h (기대값: 0xA0)", rdata), UVM_LOW)

    // ── 테스트 2: 필드 레벨 접근 ──
    `uvm_info(get_type_name(), "--- 테스트 2: 필드 접근 ---", UVM_LOW)

    // enable만 0으로 변경
    reg_model.ctrl_reg.enable.set(0);
    reg_model.ctrl_reg.update(status);

    // 읽어서 확인
    reg_model.ctrl_reg.read(status, rdata);
    `uvm_info(get_type_name(),
      $sformatf("ctrl_reg 필드 수정 후: 0x%0h (기대값: 0x20)", rdata),
      UVM_LOW)

    // ── 테스트 3: 범용 레지스터 루프 ──
    `uvm_info(get_type_name(), "--- 테스트 3: 범용 레지스터 ---", UVM_LOW)

    for (int i = 0; i < 13; i++) begin
      reg_model.gp_reg[i].write(status, i * 8'h11);
    end

    for (int i = 0; i < 13; i++) begin
      reg_model.gp_reg[i].read(status, rdata);
      if (rdata !== i * 8'h11)
        `uvm_error(get_type_name(),
          $sformatf("gp_reg[%0d] 불일치: got=0x%0h, exp=0x%0h",
                    i, rdata, i * 8'h11))
    end

    // ── 테스트 4: Mirror 확인 ──
    `uvm_info(get_type_name(), "--- 테스트 4: Mirror ---", UVM_LOW)

    reg_model.ctrl_reg.mirror(status, UVM_CHECK);
    reg_model.data_reg.mirror(status, UVM_CHECK);

    `uvm_info(get_type_name(),
      "=== RAL 레지스터 테스트 완료 ===", UVM_NONE)
  endtask
endclass
```

### 12.5.3 첫 RAL 시뮬레이션

```systemverilog
// ──────────────────────────────────────────
// RAL 테스트
// 파일: apb_ral_test.sv
// ──────────────────────────────────────────
class apb_ral_test extends uvm_test;
  `uvm_component_utils(apb_ral_test)

  apb_ral_env env;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = apb_ral_env::type_id::create("env", this);
  endfunction

  task run_phase(uvm_phase phase);
    apb_ral_test_seq seq;

    phase.raise_objection(this);

    seq = apb_ral_test_seq::type_id::create("seq");
    seq.reg_model = env.reg_model;  // 시퀀스에 레지스터 모델 전달
    seq.start(env.agent.sequencer);
    // 참고: uvm_reg_sequence는 `model` 프로퍼티를 기본 제공합니다.
    // seq.model = env.reg_model; 으로도 설정 가능하며,
    // body() 안에서 model.ctrl_reg.write(...) 형태로 접근할 수 있습니다.

    #100;
    phase.drop_objection(this);
  endtask
endclass
```

실행 결과:

```
# 실행 명령
vsim +UVM_TESTNAME=apb_ral_test

UVM_INFO @ 0ns: reporter [RNTST] Running test apb_ral_test...
UVM_INFO @ 20ns: uvm_test_top [apb_ral_test_seq] === RAL 레지스터 테스트 시작 ===
UVM_INFO @ 20ns: uvm_test_top [apb_ral_test_seq] --- 테스트 1: Write/Read ---
UVM_INFO @ 50ns: ... [apb_reg_adapter] reg2bus: WRITE addr=0x0 data=0xA0
UVM_INFO @ 80ns: ... [apb_reg_adapter] reg2bus: READ addr=0x0 data=0x0
UVM_INFO @ 80ns: uvm_test_top [apb_ral_test_seq] ctrl_reg read: 0xA0 (기대값: 0xA0)
UVM_INFO @ 80ns: uvm_test_top [apb_ral_test_seq] --- 테스트 2: 필드 접근 ---
UVM_INFO @ 110ns: ... [apb_reg_adapter] reg2bus: WRITE addr=0x0 data=0x20
UVM_INFO @ 140ns: uvm_test_top [apb_ral_test_seq] ctrl_reg 필드 수정 후: 0x20 (기대값: 0x20)
UVM_INFO @ 140ns: uvm_test_top [apb_ral_test_seq] --- 테스트 3: 범용 레지스터 ---
...
UVM_INFO @ 920ns: uvm_test_top [apb_ral_test_seq] --- 테스트 4: Mirror ---
UVM_INFO @ 960ns: uvm_test_top [apb_ral_test_seq] === RAL 레지스터 테스트 완료 ===

--- UVM Report Summary ---
UVM_INFO :   42
UVM_WARNING :   0
UVM_ERROR :   0
UVM_FATAL :   0
```

> 💡 **성취감**: RAL을 통해 `reg_model.ctrl_reg.enable.set(1)`처럼 **이름으로** 레지스터에 접근하고 있습니다! Ch.11에서 `addr=0x0, data=0x80`으로 수동 계산하던 것과 비교해보세요.

---

## 12.6 내장 시퀀스와 백도어

> **이 절의 목표**: UVM RAL의 내장 테스트 시퀀스로 자동 검증을 체험하고, Backdoor 접근을 이해합니다.

### 12.6.1 uvm_reg_hw_reset_seq — 리셋 값 검증

모든 레지스터의 리셋 값이 사양과 일치하는지 **자동으로** 검증합니다:

```systemverilog
// ──────────────────────────────────────────
// 내장 시퀀스 테스트
// 파일: apb_ral_builtin_test.sv
// ──────────────────────────────────────────
class apb_ral_reset_test extends uvm_test;
  `uvm_component_utils(apb_ral_reset_test)

  apb_ral_env env;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = apb_ral_env::type_id::create("env", this);
  endfunction

  task run_phase(uvm_phase phase);
    uvm_reg_hw_reset_seq rst_seq;

    phase.raise_objection(this);

    `uvm_info(get_type_name(),
      "=== 리셋 값 자동 검증 시작 ===", UVM_NONE)

    // 내장 시퀀스 — 1줄로 모든 레지스터 리셋 값 검증!
    rst_seq = uvm_reg_hw_reset_seq::type_id::create("rst_seq");
    rst_seq.model = env.reg_model;
    rst_seq.start(env.agent.sequencer);

    `uvm_info(get_type_name(),
      "=== 리셋 값 자동 검증 완료 ===", UVM_NONE)

    phase.drop_objection(this);
  endtask
endclass
```

**이것이 RAL의 힘입니다:**
- Ch.11에서는 16개 레지스터를 일일이 읽고 0x00과 비교해야 했습니다
- RAL에서는 **3줄**로 모든 레지스터의 리셋 값을 자동 검증합니다
- 레지스터가 3,000개여도 동일한 3줄입니다

### 12.6.2 uvm_reg_bit_bash_seq — 비트 접근 검증

모든 R/W 필드에 0과 1을 번갈아 쓰고 읽어서 **비트별 접근이 정상인지** 자동 검증합니다:

```systemverilog
task run_phase(uvm_phase phase);
  uvm_reg_bit_bash_seq bash_seq;

  phase.raise_objection(this);

  `uvm_info(get_type_name(),
    "=== 비트 배시 자동 검증 시작 ===", UVM_NONE)

  bash_seq = uvm_reg_bit_bash_seq::type_id::create("bash_seq");
  bash_seq.model = env.reg_model;
  bash_seq.start(env.agent.sequencer);

  `uvm_info(get_type_name(),
    "=== 비트 배시 자동 검증 완료 ===", UVM_NONE)

  phase.drop_objection(this);
endtask
```

**비트 배시 테스트가 검증하는 것:**
- 각 R/W 비트에 1을 쓰고 읽어서 1이 나오는지
- 각 R/W 비트에 0을 쓰고 읽어서 0이 나오는지
- R/O 비트에 쓰기가 무시되는지
- 비트들이 서로 간섭하지 않는지

> 💡 **실무 팁**: `uvm_reg_bit_bash_seq`는 레지스터 RTL의 기본적인 "연결 상태"를 검증합니다. 레지스터 접근 로직에 비트 매핑 오류가 있으면 이 시퀀스가 잡아냅니다. 실무에서 레지스터 IP의 첫 번째 검증으로 거의 반드시 실행합니다.

### 12.6.3 Backdoor 접근 — DUT 직접 읽기/쓰기

**Frontdoor**는 실제 버스(APB)를 통해 접근하지만, **Backdoor**는 시뮬레이터의 HDL 계층 경로를 통해 **직접** 레지스터에 접근합니다:

```systemverilog
// Frontdoor: 실제 APB 버스를 통해 접근 (느리지만 현실적)
reg_model.ctrl_reg.write(status, 8'hFF);  // APB 프로토콜 → 여러 클록

// Backdoor: HDL 경로를 통해 직접 접근 (빠르지만 비현실적)
reg_model.ctrl_reg.poke(status, 8'hFF);   // 0 시간에 완료
reg_model.ctrl_reg.peek(status, rdata);   // 0 시간에 완료
```

**Frontdoor vs Backdoor:**

| 특성 | Frontdoor | Backdoor |
|------|-----------|----------|
| **접근 경로** | APB 버스 (실제 프로토콜) | HDL 계층 경로 (시뮬레이터) |
| **시뮬레이션 시간** | 여러 클록 사이클 | 0 시간 (즉시) |
| **용도** | 기능 검증 (실제 동작) | 초기화, 디버깅, 빠른 설정 |
| **현실성** | 실제 하드웨어와 동일 | 실제 하드웨어에서 불가능 |
| **RAL 메서드** | `write()`, `read()` | `poke()`, `peek()` |

**Backdoor를 사용하는 대표적 상황:**

1. **테스트 초기화**: 수백 개 레지스터를 특정 값으로 빠르게 설정
2. **상태 주입**: DUT 내부 상태를 강제로 변경하여 특정 시나리오 생성
3. **디버깅**: 프로토콜 문제와 무관하게 레지스터 값 직접 확인

Backdoor 경로 설정:

```systemverilog
// 레지스터 블록의 build()에서 HDL 경로 설정
reg_model.ctrl_reg.add_hdl_path_slice(
  "tb_top.dut.mem[0]",  // RTL의 실제 HDL 경로
  0,                     // 시작 비트
  8                      // 비트 폭
);
```

**Backdoor 활용 예시:**

```systemverilog
// ── 테스트 초기화에 Backdoor 활용 ──
task setup_registers();
  uvm_status_e status;
  uvm_reg_data_t rdata;

  // Backdoor로 빠르게 초기 값 설정 (0 시간)
  reg_model.ctrl_reg.poke(status, 8'hA0);   // enable=1, mode=01
  reg_model.data_reg.poke(status, 8'hFF);

  // Frontdoor로 실제 값 확인 (APB 프로토콜 통해)
  reg_model.ctrl_reg.read(status, rdata);
  if (rdata !== 8'hA0)
    `uvm_error("BACKDOOR", "Backdoor 값과 Frontdoor 읽기 불일치!")
endtask
```

> 💡 **실무 팁**: Backdoor 경로는 RTL 구조에 의존하므로, RTL이 변경되면 경로도 수정해야 합니다. 이 때문에 Frontdoor 검증을 기본으로 하고, Backdoor는 보조 수단으로 사용합니다.

### 12.6.4 Ch.11 수동 검증 vs RAL 자동 검증 비교

```
┌─────────────────────────────────────────────────────────────┐
│         Ch.11 (수동 검증) vs Ch.12 (RAL 자동 검증)           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   검증 항목          Ch.11 (수동)         Ch.12 (RAL)       │
│                                                              │
│   레지스터 접근      주소/데이터 직접     이름으로 접근       │
│                      addr=0x0, data=0x80  ctrl_reg.write()  │
│                                                              │
│   필드 접근          비트 마스킹 수동     필드 API           │
│                      data & 8'h80        enable.set(1)      │
│                                                              │
│   리셋 값 검증       16개 루프 + 비교    hw_reset_seq 1줄   │
│                                                              │
│   비트 접근 검증     수백 줄 코딩        bit_bash_seq 1줄   │
│                                                              │
│   상태 추적          스코어보드 수동     Predictor 자동      │
│                                                              │
│   확장성             레지스터 수에 비례  모델만 추가          │
│                                                              │
│   ────────────────────────────────────────────              │
│   결론: RAL은 "레지스터 검증의 자동화 프레임워크"           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

> 💡 **핵심 교훈**: Ch.11에서 수동으로 작성한 스코어보드, Write/Read 시퀀스, 비교 로직이 RAL에서는 **프레임워크 수준에서 자동 제공**됩니다. 검증 엔지니어는 레지스터 모델만 정의하면 됩니다.

### 12.6.5 RAL 자주 하는 실수 Top 5

| 순위 | 실수 | 에러 메시지 | 해결 |
|------|------|-----------|------|
| 1 | `lock_model()` 누락 | `Register model has not been locked` | `build()` 마지막에 `lock_model()` 호출 |
| 2 | `set_sequencer()` 누락 | `No sequencer registered for map` | `connect_phase`에서 `reg_map.set_sequencer(sqr, adapter)` |
| 3 | `set_auto_predict(0)` 누락 | 미러 값 이중 업데이트 (silent bug) | Predictor 사용 시 반드시 설정 |
| 4 | 필드 비트 위치 겹침 | `Field ... overlaps with field ...` | `configure()`의 `lsb_pos`, `size` 확인 |
| 5 | Adapter의 `bus2reg()`에서 `$cast` 실패 | `bus2reg: 타입 변환 실패` | `apb_seq_item` 타입이 올바른지 확인 |

> 💡 **실무 팁**: 1번과 2번 실수가 전체 RAL 에러의 80%를 차지합니다. RAL 환경을 설정한 후 간단한 `write()`/`read()`가 동작하는지 반드시 먼저 확인하세요. 복잡한 시퀀스는 기본 동작 확인 후에 추가합니다.

---

## 12.7 체크포인트

> **이 절의 목표**: 이 챕터의 핵심 개념을 확인합니다.

### 12.7.1 셀프 체크

다음 질문에 답할 수 있으면 이 챕터의 핵심을 이해한 것입니다:

**1. RAL의 4계층 구조를 설명하세요.** (12.2)

<details>
<summary>정답 확인</summary>
① `uvm_reg_field` — 레지스터 내 개별 비트 그룹 (비트 위치, 접근 타입, 리셋 값)
② `uvm_reg` — 하나의 레지스터 (여러 field 포함)
③ `uvm_reg_block` — 여러 레지스터를 그룹으로 묶음
④ `uvm_reg_map` — 각 레지스터에 주소를 매핑
관계: Block이 Map과 Reg를 포함하고, Map이 Reg에 주소를 할당하고, Reg가 Field를 포함합니다.
</details>

**2. Adapter의 두 가지 메서드의 역할은?** (12.4)

<details>
<summary>정답 확인</summary>
① `reg2bus()` — RAL의 추상적 레지스터 읽기/쓰기 요청을 버스 트랜잭션(apb_seq_item)으로 변환합니다. RAL이 `write()`/`read()`를 호출하면 이 함수가 호출됩니다.
② `bus2reg()` — 버스 트랜잭션 완료 후 결과를 RAL에 전달합니다. Read의 경우 rdata를 RAL에 반환합니다.
</details>

**3. desired, mirrored, actual 값의 차이는?** (12.4)

<details>
<summary>정답 확인</summary>
- `desired`: RAL 모델에서 "쓰고 싶은 값". `set()` 호출 시 업데이트됩니다.
- `mirrored`: RAL 모델에서 "DUT에 있을 것으로 추정하는 값". `write()`/`read()` 완료 시 업데이트됩니다.
- `actual`: DUT 하드웨어의 실제 레지스터 값. 버스 트랜잭션이나 하드웨어 동작으로 변경됩니다.
Predictor가 모니터 관찰 결과로 mirrored를 자동 업데이트하여 actual과 동기화합니다.
</details>

**4. `lock_model()`을 호출하지 않으면 어떻게 되나요?** (12.3)

<details>
<summary>정답 확인</summary>
런타임에 `UVM_FATAL: "Register model has not been locked!"` 에러가 발생합니다. `lock_model()`은 레지스터 모델의 빌드가 완료되었음을 선언하는 메서드로, 이후에 레지스터나 맵을 추가/수정할 수 없게 잠급니다. 보통 `uvm_reg_block::build()` 함수의 마지막에 호출합니다.
</details>

**5. Frontdoor와 Backdoor 접근의 차이와 각각의 용도는?** (12.6)

<details>
<summary>정답 확인</summary>
- Frontdoor: 실제 버스(APB)를 통해 접근합니다. 여러 클록이 소요되지만 실제 하드웨어 동작과 동일합니다. 기능 검증에 사용합니다. (`write()`, `read()`)
- Backdoor: HDL 계층 경로를 통해 직접 접근합니다. 0시간에 완료되지만 실제 하드웨어에서는 불가능합니다. 초기화, 디버깅, 빠른 설정에 사용합니다. (`poke()`, `peek()`)
</details>

**6. `uvm_reg_hw_reset_seq`는 무엇을 검증하나요?** (12.6)

<details>
<summary>정답 확인</summary>
모든 레지스터의 리셋 후 값이 RAL 모델에 정의된 리셋 값과 일치하는지 자동 검증합니다. 각 레지스터를 읽고 (`read()`), 모델의 `get_reset()` 값과 비교합니다. 레지스터 수에 관계없이 3줄로 전체 검증이 가능합니다.
</details>

### 12.7.2 연습문제

**연습 12-1 (기본)**: RAL 커버리지 활성화

`apb_ctrl_reg`의 생성자에서 `UVM_NO_COVERAGE` 대신 `UVM_CVR_REG_BITS`를 사용하여 레지스터 비트 커버리지를 활성화하세요. 시뮬레이션 후 `get_coverage()` 메서드로 커버리지 결과를 확인하세요.

<details>
<summary>힌트</summary>

```systemverilog
// 생성자 변경
super.new(name, 8, UVM_CVR_REG_BITS);

// report_phase에서 확인
`uvm_info("COV", $sformatf("ctrl_reg coverage: %0d%%",
  reg_model.ctrl_reg.get_coverage(UVM_CVR_REG_BITS)), UVM_NONE)
```
</details>

**연습 12-2 (중급)**: 커스텀 레지스터 시퀀스

`uvm_reg_sequence`를 상속하여 "모든 R/W 레지스터에 0xFF를 쓰고 읽어서 비교하는" 시퀀스를 작성하세요. `reg_model.reg_map.get_registers()`로 레지스터 목록을 가져올 수 있습니다.

<details>
<summary>힌트</summary>

```systemverilog
class apb_all_ff_seq extends uvm_reg_sequence;
  task body();
    uvm_reg regs[$];
    reg_model.reg_map.get_registers(regs);
    foreach (regs[i]) begin
      if (regs[i].get_rights() == "RW") begin
        regs[i].write(status, 8'hFF);
        regs[i].mirror(status, UVM_CHECK);
      end
    end
  endtask
endclass
```
</details>

**연습 12-3 (도전)**: Backdoor 경로 설정

APB Slave Memory의 `mem[0]`~`mem[15]`에 대한 Backdoor 경로를 설정하고, `poke()`로 값을 쓴 뒤 Frontdoor `read()`로 읽어서 일치하는지 검증하세요.

<details>
<summary>힌트</summary>
`add_hdl_path_slice("tb_top.dut.mem[0]", 0, 8)`을 레지스터 블록의 `build()`에 추가합니다. `add_hdl_path()`로 레지스터 블록의 루트 경로도 설정해야 합니다.
</details>

### 12.7.3 이 챕터에서 배운 것

이 챕터에서 추가한 RAL 관련 파일:

```
apb_verification/
├── rtl/
│   └── apb_slave_memory.sv    ← Ch.11에서 만든 DUT (변경 없음)
├── tb/
│   ├── apb_if.sv              ← Ch.11 (변경 없음)
│   ├── apb_seq_item.sv        ← Ch.11 (변경 없음)
│   ├── apb_driver.sv          ← Ch.11 (변경 없음)
│   ├── apb_monitor.sv         ← Ch.11 (변경 없음)
│   ├── apb_agent.sv           ← Ch.11 (변경 없음)
│   ├── apb_reg_classes.sv     ← NEW: 레지스터 클래스 (ctrl, status, data)
│   ├── apb_reg_block.sv       ← NEW: 레지스터 블록 + 맵
│   ├── apb_reg_adapter.sv     ← NEW: Adapter (reg2bus/bus2reg)
│   ├── apb_ral_env.sv         ← NEW: RAL 통합 환경
│   ├── apb_ral_test_seq.sv    ← NEW: RAL 테스트 시퀀스
│   └── apb_ral_test.sv        ← NEW: RAL 테스트
└── sim/
    └── run.do
```

Ch.11의 APB 에이전트 코드는 **한 줄도 변경하지 않았습니다.** RAL은 기존 환경 위에 **계층을 추가**하는 것입니다.

### 12.7.4 다음 장 미리보기

Chapter 13에서는 **고급 시퀀스**를 배웁니다. 가상 시퀀스(Virtual Sequence)로 여러 에이전트를 동시에 제어하고, 시퀀스 라이브러리로 테스트 시나리오를 체계적으로 관리합니다. Ch.11의 APB 시퀀스와 Ch.12의 RAL 시퀀스가 가상 시퀀스 안에서 조합되어 더 복잡한 검증 시나리오를 구현합니다.

**Part 3 진행 현황:**

| 챕터 | 주제 | 핵심 | 상태 |
|------|------|------|------|
| **Ch.11** | 인터페이스와 BFM | APB 에이전트 구축 | ✅ 완료 |
| **Ch.12** | 레지스터 모델 (RAL) | APB 위에 RAL 계층 추가 | ✅ 지금 여기! |
| **Ch.13** | 고급 시퀀스 | 가상 시퀀스, 시퀀스 라이브러리 | 다음 |
| **Ch.14** | 검증 자동화 | 자동화 인프라 구축 | 대기 |
| **Ch.15** | 프로젝트 종합 | 전체 통합 및 리뷰 | 대기 |

> 💡 **핵심 메시지**: Ch.11에서 APB 에이전트를 만들고, Ch.12에서 그 위에 RAL을 올렸습니다. **기존 코드는 한 줄도 변경하지 않고** 새로운 기능을 추가했습니다. 이것이 UVM의 계층적 설계 철학입니다. Ch.13에서는 이 환경을 더 확장합니다.
