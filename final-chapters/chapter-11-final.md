# Chapter 11: 인터페이스와 BFM

> **이 챕터의 목표**: 4비트 카운터를 졸업하고 **APB 프로토콜**로 전환합니다. SystemVerilog 인터페이스의 clocking block과 modport를 실무 수준으로 활용하고, Bus Functional Model(BFM) 패턴으로 프로토콜 레벨 드라이버/모니터를 구현합니다.

> **선수 지식**: Chapter 3 (SystemVerilog 인터페이스), Chapter 5 (Virtual Interface), Chapter 7 (에이전트 구조), Chapter 10 (Part 2 완성)

---

## 11.1 4비트 카운터를 졸업하며

> **이 절의 목표**: Part 2에서 완성한 검증 환경의 구조가 새로운 프로토콜에 그대로 적용됨을 이해하고, APB 프로토콜을 소개합니다.

### 11.1.1 Part 2에서 배운 것 — 구조는 같다

Ch.5~Ch.10에서 4비트 카운터 하나로 UVM 검증의 핵심 사이클을 완성했습니다:

```
테스트 → 환경 → 에이전트 → {드라이버, 모니터, 시퀀서}
                    → 스코어보드 → 커버리지
```

이 구조는 DUT가 4비트 카운터든 SoC의 복잡한 IP든 **동일합니다**. Part 3에서 바뀌는 것은:

| 요소 | Part 2 (4비트 카운터) | Part 3 (APB 프로토콜) |
|------|----------------------|----------------------|
| **DUT** | `counter_4bit` | `apb_slave_memory` |
| **인터페이스** | `counter_if` (3신호) | `apb_if` (9+신호) |
| **트랜잭션** | `counter_seq_item` (rst_n, enable) | `apb_seq_item` (addr, data, write) |
| **드라이버** | 직접 신호 대입 | **프로토콜 핸드셰이크** |
| **모니터** | 단순 샘플링 | **프로토콜 phase 추적** |
| **스코어보드** | 카운터 예측 모델 | **메모리 모델** |
| **UVM 구조** | 동일 | **동일** |

핵심 메시지: **UVM 구조는 바뀌지 않습니다.** 바뀌는 것은 인터페이스와 프로토콜 로직뿐입니다.

### 11.1.2 실무 프로토콜이란? — APB 소개

**APB (Advanced Peripheral Bus)**는 ARM AMBA(Advanced Microcontroller Bus Architecture) 표준의 일부입니다. SoC에서 가장 단순한 버스 프로토콜로, 거의 모든 IP 블록의 레지스터 접근에 사용됩니다.

**왜 APB인가?**

1. **단순함**: 2 phase (Setup → Access)로 동작하며, 파이프라인 없음
2. **실무 필수**: 팹리스 회사의 모든 SoC에 APB 인터페이스 존재
3. **RAL 기반**: Ch.12의 레지스터 모델(RAL)이 APB 위에서 동작
4. **면접 빈출**: "APB 프로토콜을 설명하세요"는 검증 엔지니어 면접의 기본 질문

**APB 신호:**

| 신호 | 방향 | 폭 | 설명 |
|------|------|------|------|
| `pclk` | — | 1 | 클록 |
| `presetn` | — | 1 | 리셋 (액티브 로우) |
| `psel` | Master→Slave | 1 | 슬레이브 선택 |
| `penable` | Master→Slave | 1 | 전송 활성화 (Access phase) |
| `pwrite` | Master→Slave | 1 | 1=쓰기, 0=읽기 |
| `paddr` | Master→Slave | 4 | 주소 (4비트 = 16개 레지스터) |
| `pwdata` | Master→Slave | 8 | 쓰기 데이터 (8비트) |
| `prdata` | Slave→Master | 8 | 읽기 데이터 (8비트) |
| `pready` | Slave→Master | 1 | 슬레이브 준비 완료 |

> 💡 **면접 팁**: APB 신호 이름은 모두 `p`로 시작합니다. 이것은 AMBA 표준의 네이밍 규칙이며, AXI는 `a`로 시작합니다 (예: `arvalid`, `awready`).

### 11.1.3 APB 프로토콜 기본 동작

APB 전송은 항상 2 phase로 동작합니다:

```
┌───────────────────────────────────────────────────────────────┐
│             APB Write / Read 프로토콜 타이밍                   │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│   ── Write 전송 ──                 ── Read 전송 ──            │
│                                                               │
│   clk     ─┐ ┌─┐ ┌─┐              clk     ─┐ ┌─┐ ┌─┐       │
│            └─┘ └─┘ └─              │        └─┘ └─┘ └─       │
│                                                               │
│   psel    ───┐     ┌───            psel    ───┐     ┌───     │
│              └─────┘               │          └─────┘        │
│                                                               │
│   penable ───────┐ ┌───            penable ───────┐ ┌───     │
│                  └─┘               │              └─┘        │
│                                                               │
│   pwrite  ───┐     ┌───            pwrite  ──────────────     │
│      (=1)    └─────┘               │  (=0)                   │
│                                                               │
│   paddr   ══╡ADDR ╞════            paddr   ══╡ADDR ╞════     │
│                                                               │
│   pwdata  ══╡DATA ╞════            prdata  ────╡DATA╞────     │
│                                                               │
│   pready  ─────────┐               pready  ─────────┐        │
│      (=1)          └─              │  (=1)          └─       │
│                                                               │
│           ↑        ↑                        ↑        ↑        │
│         Setup   Access                    Setup   Access      │
│         Phase   Phase                     Phase   Phase       │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**2 Phase 동작:**

1. **Setup Phase** (첫 번째 클록):
   - `psel = 1` — 슬레이브 선택
   - `pwrite`, `paddr`, `pwdata` 설정
   - `penable = 0` — 아직 활성화 아님

2. **Access Phase** (두 번째 클록):
   - `penable = 1` — 전송 활성화
   - `pready = 1` — 슬레이브가 준비 완료 응답
   - Write: 슬레이브가 `pwdata`를 저장
   - Read: 슬레이브가 `prdata`에 데이터 출력
   - 전송 완료 → `psel = 0`, `penable = 0`

> 💡 **실무 팁**: `pready`가 0이면 **wait state**입니다. 슬레이브가 아직 준비되지 않았다는 의미이며, Access phase가 연장됩니다. 이 챕터에서는 항상 `pready = 1` (no wait state)로 시작하고, wait state 처리는 연습문제에서 다룹니다.

---

## 11.2 SystemVerilog 인터페이스 심화

> **이 절의 목표**: Ch.3에서 배운 인터페이스의 clocking block과 modport를 실무 수준으로 활용하여 APB 인터페이스를 설계합니다.

### 11.2.1 Clocking Block — 타이밍 안전한 신호 접근

Ch.5~10에서는 드라이버가 인터페이스 신호에 직접 접근했습니다:

```systemverilog
// Part 2 방식 — 직접 신호 접근
@(posedge vif.clk);
vif.rst_n  <= item.rst_n;
vif.enable <= item.enable;
```

이 방식은 간단한 카운터에서는 문제없지만, 실무 프로토콜에서는 **타이밍 문제**가 발생할 수 있습니다. Clocking block은 이를 해결합니다:

```systemverilog
// Part 3 방식 — clocking block을 통한 안전한 접근
@(vif.drv_cb);              // clocking block 이벤트 대기
vif.drv_cb.psel    <= 1'b1; // output은 clocking block을 통해 구동
vif.drv_cb.pwrite  <= 1'b1;
vif.drv_cb.paddr   <= item.addr;
vif.drv_cb.pwdata  <= item.data;
```

**Clocking block의 장점:**

| 특성 | 직접 접근 | Clocking Block |
|------|----------|---------------|
| **타이밍** | 수동 `@(posedge clk)` | 자동 동기화 |
| **경쟁 조건** | 가능 | 방지 |
| **방향 제어** | 없음 | `input`/`output` 명시 |
| **실무 사용** | 학습용 | 표준 방식 |

**Clocking block은 "이 신호를 언제, 어떤 방향으로 접근하는지"를 명확히 정의합니다.**

> 💡 **심화 참고**: Clocking block은 내부적으로 `input` 신호에 `#1step` 지연을 적용합니다. 이는 "클록 에지 직전의 안정된 값"을 읽어오는 메커니즘으로, 동일 시점의 `output`과 `input` 사이의 경쟁 조건을 방지합니다. 이 챕터에서는 개념만 알아두면 충분하며, 자세한 타이밍은 시뮬레이터 매뉴얼을 참고하세요.

### 11.2.2 Modport — 드라이버/모니터 접근 제어

Modport는 인터페이스 사용자별로 **접근 권한**을 분리합니다:

```systemverilog
// 드라이버: 출력(구동)만 가능
modport driver(clocking drv_cb, input pclk, input presetn);

// 모니터: 입력(관찰)만 가능
modport monitor(clocking mon_cb, input pclk, input presetn);
```

**왜 modport가 필요한가?**

- **안전성**: 모니터가 실수로 신호를 구동하는 것을 컴파일 타임에 방지
- **가독성**: 코드를 읽을 때 각 컴포넌트의 역할이 명확
- **재사용**: 인터페이스를 다른 프로젝트에서 재사용할 때 사용법이 명확

### 11.2.3 APB 인터페이스 설계 (apb_if)

```systemverilog
// ──────────────────────────────────────────
// APB 인터페이스 정의
// 파일: apb_if.sv
// 역할: APB 프로토콜 신호 번들 + clocking block + modport
// ──────────────────────────────────────────
interface apb_if(input logic pclk, input logic presetn);

  // ── APB 신호 선언 ──
  logic        psel;      // 슬레이브 선택
  logic        penable;   // 전송 활성화
  logic        pwrite;    // 1=Write, 0=Read
  logic [3:0]  paddr;     // 주소 (16개 레지스터)
  logic [7:0]  pwdata;    // 쓰기 데이터
  logic [7:0]  prdata;    // 읽기 데이터
  logic        pready;    // 슬레이브 준비 완료

  // ── 드라이버용 Clocking Block ──
  // Master 역할: psel, penable, pwrite, paddr, pwdata를 구동
  //              prdata, pready를 관찰
  clocking drv_cb @(posedge pclk);
    output psel, penable, pwrite, paddr, pwdata;
    input  prdata, pready;
  endclocking

  // ── 모니터용 Clocking Block ──
  // 관찰자 역할: 모든 신호를 입력으로 관찰
  clocking mon_cb @(posedge pclk);
    input psel, penable, pwrite, paddr, pwdata;
    input prdata, pready;
  endclocking

  // ── Modport 정의 ──
  modport driver(clocking drv_cb, input pclk, input presetn);
  modport monitor(clocking mon_cb, input pclk, input presetn);

endinterface
```

**설계 원칙:**
- **드라이버 clocking block**: APB Master 역할의 출력 신호를 `output`, 슬레이브 응답을 `input`
- **모니터 clocking block**: 모든 신호를 `input`으로 관찰만
- **Modport**: 각 UVM 컴포넌트가 자신의 역할에 맞는 clocking block만 접근

### 11.2.4 counter_if vs apb_if 비교

| 요소 | `counter_if` (Part 2) | `apb_if` (Part 3) |
|------|----------------------|-------------------|
| **신호 수** | 3 (rst_n, enable, count) | 9 (psel, penable, ...) |
| **Clocking Block** | 없음 (직접 접근) | drv_cb, mon_cb |
| **Modport** | 없음 | driver, monitor |
| **프로토콜** | 없음 (단순 제어) | APB 2-phase handshake |
| **재사용성** | 이 프로젝트 전용 | 다른 APB DUT에도 재사용 |

**핵심 차이**: `counter_if`는 "어떤 신호가 있는가"만 정의했지만, `apb_if`는 "누가 어떤 신호를 어떤 타이밍에 접근하는가"까지 정의합니다.

---

## 11.3 APB Slave DUT

> **이 절의 목표**: APB 프로토콜을 따르는 간단한 Slave Memory DUT를 이해하고, UVM 트랜잭션과 테스트벤치 top을 설계합니다.

### 11.3.1 APB Slave Memory RTL

```systemverilog
// ──────────────────────────────────────────
// APB Slave Memory — 16 x 8-bit 레지스터
// 파일: apb_slave_memory.sv
// 역할: APB 프로토콜로 접근하는 간단한 메모리
// ──────────────────────────────────────────
module apb_slave_memory (
  input  logic        pclk,
  input  logic        presetn,
  input  logic        psel,
  input  logic        penable,
  input  logic        pwrite,
  input  logic [3:0]  paddr,
  input  logic [7:0]  pwdata,
  output logic [7:0]  prdata,
  output logic        pready
);

  // 16개의 8비트 레지스터
  logic [7:0] mem [0:15];

  // 항상 ready (no wait state)
  assign pready = 1'b1;

  // Write 동작 — Access phase에서 데이터 저장
  always_ff @(posedge pclk or negedge presetn) begin
    if (!presetn) begin
      // 리셋: 모든 레지스터를 0으로 초기화
      for (int i = 0; i < 16; i++)
        mem[i] <= 8'h0;
    end
    else if (psel && penable && pwrite && pready) begin
      // APB Write: Setup + Access phase 완료 시점에 저장
      mem[paddr] <= pwdata;
    end
  end

  // Read 동작 — 조합 로직으로 데이터 출력
  assign prdata = (psel && !pwrite) ? mem[paddr] : 8'h0;

endmodule
```

이 DUT는 Part 2의 4비트 카운터보다 복잡하지만, APB 프로토콜의 핵심을 담고 있습니다:
- **Write**: `psel=1, penable=1, pwrite=1` 조건에서 `mem[paddr] <= pwdata`
- **Read**: `psel=1, pwrite=0` 조건에서 `prdata = mem[paddr]`
- **Reset**: 모든 레지스터를 0으로 초기화

### 11.3.2 APB 트랜잭션 정의 (apb_seq_item)

```systemverilog
// ──────────────────────────────────────────
// APB 트랜잭션 클래스
// 파일: apb_seq_item.sv
// 역할: APB 전송 1건을 표현하는 UVM 트랜잭션
// ──────────────────────────────────────────
class apb_seq_item extends uvm_sequence_item;
  `uvm_object_utils(apb_seq_item)

  // ── 트랜잭션 필드 ──
  rand bit        write;    // 1=Write, 0=Read
  rand bit [3:0]  addr;     // 레지스터 주소 (0~15)
  rand bit [7:0]  wdata;    // 쓰기 데이터
       bit [7:0]  rdata;    // 읽기 데이터 (DUT 응답, rand 아님)

  // ── 기본 제약 ──
  constraint c_addr {
    addr inside {[0:15]};   // 유효 주소 범위
  }

  function new(string name = "apb_seq_item");
    super.new(name);
  endfunction

  // convert2string — 로그에서 트랜잭션 내용을 읽기 쉽게 출력
  function string convert2string();
    if (write)
      return $sformatf("APB WRITE: addr=0x%0h, wdata=0x%0h", addr, wdata);
    else
      return $sformatf("APB READ:  addr=0x%0h, rdata=0x%0h", addr, rdata);
  endfunction
endclass
```

**Part 2 `counter_seq_item`과의 비교:**

| 필드 | `counter_seq_item` | `apb_seq_item` |
|------|-------------------|----------------|
| 입력 | `rst_n`, `enable` (각 1비트) | `write`, `addr`, `wdata` |
| 출력 | 없음 (모니터가 count 관찰) | `rdata` (Read 응답) |
| 의미 | "리셋할까? 카운트할까?" | "어디에 무엇을 쓸까/읽을까?" |

### 11.3.3 tb_top — DUT와 인터페이스 연결

```systemverilog
// ──────────────────────────────────────────
// 테스트벤치 Top 모듈
// 파일: tb_top.sv
// 역할: DUT, 인터페이스, UVM 연결
// ──────────────────────────────────────────
module tb_top;
  // 클록 생성
  logic pclk;
  initial pclk = 0;
  always #5 pclk = ~pclk;  // 10ns 주기 (100MHz)

  // 리셋 생성
  logic presetn;
  initial begin
    presetn = 0;
    #20 presetn = 1;  // 20ns 후 리셋 해제
  end

  // APB 인터페이스 인스턴스
  apb_if apb_intf(pclk, presetn);

  // DUT 인스턴스
  apb_slave_memory dut (
    .pclk    (pclk),
    .presetn (presetn),
    .psel    (apb_intf.psel),
    .penable (apb_intf.penable),
    .pwrite  (apb_intf.pwrite),
    .paddr   (apb_intf.paddr),
    .pwdata  (apb_intf.pwdata),
    .prdata  (apb_intf.prdata),
    .pready  (apb_intf.pready)
  );

  initial begin
    // VCD 파형 덤프 (Ch.10에서 배운 디버깅용)
    $dumpfile("apb_debug.vcd");
    $dumpvars(0, tb_top);

    // config_db에 인터페이스 등록 (Ch.5에서 배운 패턴)
    uvm_config_db#(virtual apb_if)::set(
      null, "uvm_test_top.*", "vif", apb_intf);

    // UVM 테스트 실행
    run_test();
  end
endmodule
```

**구조는 Ch.5의 `tb_top`과 동일합니다.** `counter_if` → `apb_if`, `counter_4bit` → `apb_slave_memory`로 교체했을 뿐입니다.

---

## 11.4 Bus Functional Model (BFM) 패턴

> **이 절의 목표**: BFM 패턴을 이해하고, APB 프로토콜의 Write/Read를 구현하는 드라이버와 모니터를 작성합니다.

### 11.4.1 BFM이란? — 프로토콜 행위를 캡슐화

Part 2에서 카운터 드라이버는 이렇게 동작했습니다:

```systemverilog
// Part 2: 카운터 드라이버 — 직접 신호 대입
@(posedge vif.clk);
vif.rst_n  <= item.rst_n;
vif.enable <= item.enable;
// 끝! 1클록이면 완료
```

하지만 APB 프로토콜은 **여러 클록에 걸친 핸드셰이크**가 필요합니다:

```systemverilog
// Part 3: APB 드라이버 — 프로토콜 핸드셰이크
// Setup Phase (1클록)
@(vif.drv_cb);
vif.drv_cb.psel    <= 1'b1;
vif.drv_cb.pwrite  <= item.write;
vif.drv_cb.paddr   <= item.addr;
vif.drv_cb.pwdata  <= item.wdata;

// Access Phase (1클록 이상)
@(vif.drv_cb);
vif.drv_cb.penable <= 1'b1;
while (vif.drv_cb.pready !== 1'b1)  // 슬레이브 응답 대기
  @(vif.drv_cb);

// 전송 완료
@(vif.drv_cb);
vif.drv_cb.psel    <= 1'b0;
vif.drv_cb.penable <= 1'b0;
```

**Bus Functional Model(BFM)**은 이러한 프로토콜 행위를 **task로 캡슐화**하는 패턴입니다:

| 관점 | 직접 신호 대입 | BFM 패턴 |
|------|--------------|---------|
| **추상화** | 비트 레벨 | 트랜잭션 레벨 |
| **복잡도** | 신호마다 코딩 | `drive_write(addr, data)` 호출 |
| **재사용** | DUT마다 새로 작성 | 프로토콜 한 번 구현, 재사용 |
| **유지보수** | 프로토콜 변경 시 전체 수정 | BFM task만 수정 |

**BFM이 필요한 이유**: "어떤 값을 보낼까?"(시퀀스의 역할)와 "어떻게 보낼까?"(프로토콜의 역할)를 분리합니다.

**구체적 시나리오**: 프로토콜 사양이 변경되어 APB에 `pslverr` (에러 응답) 신호가 추가된다고 가정합시다:
- **직접 신호 대입 방식**: 10개 시퀀스의 모든 `@(posedge clk)` 블록에서 `pslverr` 처리를 추가해야 합니다 → 10곳 수정
- **BFM 방식**: `drive_transfer()` task 1개만 수정하면 됩니다 → 1곳 수정

프로토콜이 복잡해질수록 BFM의 가치가 커집니다. 실무에서 AXI 프로토콜은 5개 채널에 수십 개 신호가 있으며, BFM 없이는 시퀀스 작성이 사실상 불가능합니다.

### 11.4.2 APB Master Driver — Write/Read 프로토콜 구현

```systemverilog
// ──────────────────────────────────────────
// APB Master Driver
// 파일: apb_driver.sv
// 역할: 시퀀서로부터 트랜잭션을 받아 APB 프로토콜로 인터페이스 구동
// ──────────────────────────────────────────
class apb_driver extends uvm_driver #(apb_seq_item);
  `uvm_component_utils(apb_driver)

  virtual apb_if.driver vif;  // modport 타입으로 선언

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual apb_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "config_db::get failed for 'vif'")
  endfunction

  // ── 메인 드라이빙 루프 ──
  task run_phase(uvm_phase phase);
    // 리셋 대기
    @(posedge vif.presetn);
    `uvm_info(get_type_name(), "리셋 해제 감지, 드라이빙 시작", UVM_LOW)

    forever begin
      apb_seq_item item;
      seq_item_port.get_next_item(item);

      // ── BFM: APB 프로토콜 구동 ──
      drive_transfer(item);

      `uvm_info(get_type_name(),
        $sformatf("전송 완료: %s", item.convert2string()), UVM_MEDIUM)

      seq_item_port.item_done();
    end
  endtask

  // ── BFM Task: APB 전송 1건 구동 ──
  virtual task drive_transfer(apb_seq_item item);
    // [1] Setup Phase
    @(vif.drv_cb);
    vif.drv_cb.psel    <= 1'b1;
    vif.drv_cb.penable <= 1'b0;
    vif.drv_cb.pwrite  <= item.write;
    vif.drv_cb.paddr   <= item.addr;
    if (item.write)
      vif.drv_cb.pwdata <= item.wdata;

    // [2] Access Phase
    @(vif.drv_cb);
    vif.drv_cb.penable <= 1'b1;

    // pready 대기 (no wait state면 즉시 통과)
    while (vif.drv_cb.pready !== 1'b1)
      @(vif.drv_cb);

    // Read 응답 캡처
    if (!item.write)
      item.rdata = vif.drv_cb.prdata;

    // [3] 전송 완료 — 버스 해제
    @(vif.drv_cb);
    vif.drv_cb.psel    <= 1'b0;
    vif.drv_cb.penable <= 1'b0;
  endtask

endclass
```

**핵심 포인트:**
- `drive_transfer()` task가 **BFM**입니다 — APB 프로토콜을 한 곳에 캡슐화
- `virtual apb_if.driver vif` — modport 타입으로 접근 제한
- `@(vif.drv_cb)` — clocking block 이벤트로 동기화
- Read 시 `item.rdata`에 응답을 저장하여 시퀀스에 전달

### 11.4.3 APB Monitor — 프로토콜 관찰과 트랜잭션 추출

```systemverilog
// ──────────────────────────────────────────
// APB Monitor
// 파일: apb_monitor.sv
// 역할: APB 버스를 관찰하여 트랜잭션 추출, analysis port로 전송
// ──────────────────────────────────────────
class apb_monitor extends uvm_monitor;
  `uvm_component_utils(apb_monitor)

  virtual apb_if.monitor vif;  // monitor modport
  uvm_analysis_port #(apb_seq_item) ap;  // 스코어보드/커버리지로 전송

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    ap = new("ap", this);
    if (!uvm_config_db#(virtual apb_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "config_db::get failed for 'vif'")
  endfunction

  // ── 프로토콜 관찰 루프 ──
  task run_phase(uvm_phase phase);
    @(posedge vif.presetn);  // 리셋 해제 대기

    forever begin
      apb_seq_item item;

      // Access Phase 완료 시점 감지
      // psel=1, penable=1, pready=1이면 전송 완료
      @(vif.mon_cb);
      if (vif.mon_cb.psel && vif.mon_cb.penable && vif.mon_cb.pready) begin
        item = apb_seq_item::type_id::create("item");

        // 트랜잭션 정보 추출
        item.write = vif.mon_cb.pwrite;
        item.addr  = vif.mon_cb.paddr;
        item.wdata = vif.mon_cb.pwdata;
        item.rdata = vif.mon_cb.prdata;

        `uvm_info(get_type_name(),
          $sformatf("관찰: %s", item.convert2string()), UVM_HIGH)

        // analysis port로 전송 (스코어보드, 커버리지가 수신)
        ap.write(item);
      end
    end
  endtask

endclass
```

**모니터의 핵심:**
- `psel && penable && pready` — APB 전송 완료 조건
- 모니터는 **버스에 영향을 주지 않고** 관찰만 합니다 (modport monitor)
- `ap.write(item)` — Ch.8에서 배운 analysis port 패턴

### 11.4.4 counter_driver vs apb_driver 비교

| 요소 | `counter_driver` (Part 2) | `apb_driver` (Part 3) |
|------|--------------------------|----------------------|
| **인터페이스** | `virtual counter_if vif` | `virtual apb_if.driver vif` |
| **동기화** | `@(posedge vif.clk)` | `@(vif.drv_cb)` |
| **신호 접근** | `vif.rst_n <= ...` | `vif.drv_cb.psel <= ...` |
| **프로토콜** | 1클록 완료 | 2+클록 핸드셰이크 |
| **BFM task** | 없음 (직접 대입) | `drive_transfer()` |
| **UVM 구조** | `uvm_driver #(T)` | `uvm_driver #(T)` ← **동일!** |

UVM 프레임워크 레벨에서는 **완전히 동일한 패턴**입니다. 바뀐 것은 `drive_transfer()` 내부의 프로토콜 로직뿐입니다.

---

## 11.5 APB 에이전트 조립

> **이 절의 목표**: 드라이버, 모니터, 시퀀서를 APB 에이전트로 조립하고, 환경과 테스트 클래스를 구성합니다.

### 11.5.1 apb_agent — 드라이버, 모니터, 시퀀서 통합

```systemverilog
// ──────────────────────────────────────────
// APB Agent
// 파일: apb_agent.sv
// 역할: APB 드라이버, 모니터, 시퀀서를 하나의 재사용 단위로 묶음
// ──────────────────────────────────────────
class apb_agent extends uvm_agent;
  `uvm_component_utils(apb_agent)

  apb_driver    driver;
  apb_monitor   monitor;
  uvm_sequencer #(apb_seq_item) sequencer;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // Ch.7에서 배운 패턴과 동일!
    monitor = apb_monitor::type_id::create("monitor", this);

    if (get_is_active() == UVM_ACTIVE) begin
      driver    = apb_driver::type_id::create("driver", this);
      sequencer = uvm_sequencer#(apb_seq_item)::type_id::create("sequencer", this);
    end
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);

    if (get_is_active() == UVM_ACTIVE) begin
      driver.seq_item_port.connect(sequencer.seq_item_export);
    end
  endfunction
endclass
```

**Ch.7의 `counter_agent`와 구조가 동일합니다.** 타입만 `counter_*` → `apb_*`로 변경했습니다.

### 11.5.2 apb_env와 apb_base_test

```systemverilog
// ──────────────────────────────────────────
// APB 환경
// 파일: apb_env.sv
// 역할: APB 에이전트와 스코어보드를 포함하는 검증 환경
// ──────────────────────────────────────────
class apb_env extends uvm_env;
  `uvm_component_utils(apb_env)

  apb_agent      agent;
  apb_scoreboard scoreboard;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    agent      = apb_agent::type_id::create("agent", this);
    scoreboard = apb_scoreboard::type_id::create("scoreboard", this);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    // 모니터의 analysis port → 스코어보드
    agent.monitor.ap.connect(scoreboard.ap_imp);
  endfunction
endclass
```

```systemverilog
// ──────────────────────────────────────────
// APB Base Test
// 파일: apb_base_test.sv
// 역할: Ch.9에서 배운 base_test 패턴 — 공통 설정 포함
// ──────────────────────────────────────────
class apb_base_test extends uvm_test;
  `uvm_component_utils(apb_base_test)

  apb_env env;
  virtual apb_if vif;  // 리셋 대기에 사용

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = apb_env::type_id::create("env", this);
    if (!uvm_config_db#(virtual apb_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "config_db::get failed for 'vif'")
  endfunction

  // 리셋 대기 — Ch.9에서 배운 virtual task 패턴
  virtual task wait_for_reset();
    @(posedge vif.presetn);
    `uvm_info(get_type_name(), "리셋 해제 확인", UVM_LOW)
  endtask
endclass
```

### 11.5.3 첫 APB 시뮬레이션 — Write & Read 테스트

```systemverilog
// ──────────────────────────────────────────
// APB Write 시퀀스
// 파일: apb_sequences.sv
// ──────────────────────────────────────────
class apb_write_seq extends uvm_sequence #(apb_seq_item);
  `uvm_object_utils(apb_write_seq)

  // 외부에서 설정할 주소와 데이터
  bit [3:0] target_addr;
  bit [7:0] target_data;

  function new(string name = "apb_write_seq");
    super.new(name);
  endfunction

  task body();
    apb_seq_item item;
    item = apb_seq_item::type_id::create("item");

    start_item(item);
    item.write = 1;
    item.addr  = target_addr;
    item.wdata = target_data;
    finish_item(item);

    `uvm_info(get_type_name(),
      $sformatf("Write 완료: addr=0x%0h, data=0x%0h",
                target_addr, target_data), UVM_LOW)
  endtask
endclass

// ──────────────────────────────────────────
// APB Read 시퀀스
// ──────────────────────────────────────────
class apb_read_seq extends uvm_sequence #(apb_seq_item);
  `uvm_object_utils(apb_read_seq)

  bit [3:0] target_addr;
  bit [7:0] read_data;  // 결과 저장

  function new(string name = "apb_read_seq");
    super.new(name);
  endfunction

  task body();
    apb_seq_item item;
    item = apb_seq_item::type_id::create("item");

    start_item(item);
    item.write = 0;
    item.addr  = target_addr;
    finish_item(item);

    read_data = item.rdata;  // 드라이버가 채운 응답

    `uvm_info(get_type_name(),
      $sformatf("Read 완료: addr=0x%0h, data=0x%0h",
                target_addr, read_data), UVM_LOW)
  endtask
endclass

// ──────────────────────────────────────────
// APB Write-then-Read 시퀀스
// ──────────────────────────────────────────
class apb_write_read_seq extends uvm_sequence #(apb_seq_item);
  `uvm_object_utils(apb_write_read_seq)

  function new(string name = "apb_write_read_seq");
    super.new(name);
  endfunction

  task body();
    apb_write_seq wr_seq;
    apb_read_seq  rd_seq;

    // 주소 0x3에 0xAB 쓰기
    wr_seq = apb_write_seq::type_id::create("wr_seq");
    wr_seq.target_addr = 4'h3;
    wr_seq.target_data = 8'hAB;
    wr_seq.start(m_sequencer);

    // 같은 주소에서 읽기
    rd_seq = apb_read_seq::type_id::create("rd_seq");
    rd_seq.target_addr = 4'h3;
    rd_seq.start(m_sequencer);

    // 검증: 쓴 값과 읽은 값이 같아야 함
    if (rd_seq.read_data === 8'hAB)
      `uvm_info(get_type_name(), "Write-Read 일치! ✓", UVM_LOW)
    else
      `uvm_error(get_type_name(),
        $sformatf("Write-Read 불일치! wrote=0xAB, read=0x%0h",
                  rd_seq.read_data))
  endtask
endclass
```

```systemverilog
// ──────────────────────────────────────────
// 첫 APB 테스트
// 파일: apb_write_read_test.sv
// ──────────────────────────────────────────
class apb_write_read_test extends apb_base_test;
  `uvm_component_utils(apb_write_read_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  task run_phase(uvm_phase phase);
    apb_write_read_seq seq;

    phase.raise_objection(this);

    `uvm_info(get_type_name(), "=== APB Write-Read 테스트 시작 ===", UVM_NONE)

    seq = apb_write_read_seq::type_id::create("seq");
    seq.start(env.agent.sequencer);

    #100;  // 추가 대기

    `uvm_info(get_type_name(), "=== APB Write-Read 테스트 완료 ===", UVM_NONE)

    phase.drop_objection(this);
  endtask
endclass
```

실행 결과:

```
# 실행 명령
vsim +UVM_TESTNAME=apb_write_read_test

UVM_INFO @ 0ns: reporter [RNTST] Running test apb_write_read_test...
UVM_INFO @ 20ns: uvm_test_top [apb_write_read_test] === APB Write-Read 테스트 시작 ===
UVM_INFO @ 20ns: uvm_test_top.env.agent.driver [apb_driver] 리셋 해제 감지, 드라이빙 시작
UVM_INFO @ 40ns: uvm_test_top.env.agent.driver [apb_driver]
  전송 완료: APB WRITE: addr=0x3, wdata=0xAB
UVM_INFO @ 40ns: uvm_test_top [apb_write_seq] Write 완료: addr=0x3, data=0xAB
UVM_INFO @ 70ns: uvm_test_top.env.agent.driver [apb_driver]
  전송 완료: APB READ:  addr=0x3, rdata=0xAB
UVM_INFO @ 70ns: uvm_test_top [apb_read_seq] Read 완료: addr=0x3, data=0xAB
UVM_INFO @ 70ns: uvm_test_top [apb_write_read_seq] Write-Read 일치! ✓
UVM_INFO @ 170ns: uvm_test_top [apb_write_read_test] === APB Write-Read 테스트 완료 ===

--- UVM Report Summary ---
UVM_INFO :   8
UVM_WARNING :   0
UVM_ERROR :   0
UVM_FATAL :   0
```

---

## 11.6 실전: APB Write/Read 검증

> **이 절의 목표**: APB 스코어보드로 자동 검증을 구현하고, Part 2 → Part 3 구조 비교를 통해 학습을 정리합니다.

### 11.6.1 APB 시퀀스 — 다양한 시나리오

```systemverilog
// ──────────────────────────────────────────
// APB 종합 시퀀스 — 예제 11-1
// 파일: apb_full_test_seq.sv
// 역할: 모든 레지스터에 Write → Read → 비교
// ──────────────────────────────────────────
class apb_full_test_seq extends uvm_sequence #(apb_seq_item);
  `uvm_object_utils(apb_full_test_seq)

  function new(string name = "apb_full_test_seq");
    super.new(name);
  endfunction

  task body();
    apb_write_seq wr_seq;
    apb_read_seq  rd_seq;

    `uvm_info(get_type_name(),
      "=== 전체 레지스터 Write/Read 테스트 시작 ===", UVM_NONE)

    // 16개 레지스터에 순차 쓰기
    for (int i = 0; i < 16; i++) begin
      wr_seq = apb_write_seq::type_id::create($sformatf("wr_%0d", i));
      wr_seq.target_addr = i[3:0];
      wr_seq.target_data = i[7:0] * 8'h10 + 8'h01;  // 0x01, 0x11, 0x21, ...
      wr_seq.start(m_sequencer);
    end

    // 16개 레지스터에서 순차 읽기 & 검증
    for (int i = 0; i < 16; i++) begin
      rd_seq = apb_read_seq::type_id::create($sformatf("rd_%0d", i));
      rd_seq.target_addr = i[3:0];
      rd_seq.start(m_sequencer);
    end

    `uvm_info(get_type_name(),
      "=== 전체 레지스터 Write/Read 테스트 완료 ===", UVM_NONE)
  endtask
endclass
```

### 11.6.2 APB 스코어보드 — 메모리 모델 기반 비교

```systemverilog
// ──────────────────────────────────────────
// APB Scoreboard
// 파일: apb_scoreboard.sv
// 역할: 내부 메모리 모델로 DUT 동작을 예측하고 비교
// ──────────────────────────────────────────
class apb_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(apb_scoreboard)

  // analysis implementation port (Ch.8 패턴)
  uvm_analysis_imp #(apb_seq_item, apb_scoreboard) ap_imp;

  // ── Reference Model: 내부 메모리 ──
  logic [7:0] ref_mem [0:15];

  int write_count;
  int read_count;
  int match_count;
  int error_count;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    ap_imp = new("ap_imp", this);

    // 메모리 초기화
    for (int i = 0; i < 16; i++)
      ref_mem[i] = 8'h0;
  endfunction

  // ── 트랜잭션 수신 시 호출 ──
  function void write(apb_seq_item item);
    if (item.write) begin
      // Write: Reference Model 업데이트
      ref_mem[item.addr] = item.wdata;
      write_count++;

      `uvm_info(get_type_name(),
        $sformatf("WRITE: addr=0x%0h, data=0x%0h → ref_mem 업데이트",
                  item.addr, item.wdata), UVM_HIGH)
    end
    else begin
      // Read: Reference Model과 비교
      logic [7:0] expected = ref_mem[item.addr];
      read_count++;

      if (expected === item.rdata) begin
        match_count++;
        `uvm_info(get_type_name(),
          $sformatf("READ MATCH: addr=0x%0h, expected=0x%0h, actual=0x%0h ✓",
                    item.addr, expected, item.rdata), UVM_MEDIUM)
      end
      else begin
        error_count++;
        `uvm_error(get_type_name(),
          $sformatf("READ MISMATCH: addr=0x%0h, expected=0x%0h, actual=0x%0h",
                    item.addr, expected, item.rdata))
      end
    end
  endfunction

  // ── 결과 보고 (Ch.8 패턴) ──
  function void report_phase(uvm_phase phase);
    `uvm_info(get_type_name(),
      $sformatf("\n=== APB Scoreboard 결과 ===\n  Write: %0d건\n  Read:  %0d건 (Match: %0d, Error: %0d)\n  결과: %s",
                write_count, read_count, match_count, error_count,
                (error_count == 0) ? "PASS ✓" : "FAIL ✗"), UVM_NONE)
  endfunction
endclass
```

**Ch.8의 `counter_scoreboard`와 비교:**

| 요소 | `counter_scoreboard` | `apb_scoreboard` |
|------|---------------------|-----------------|
| **Reference Model** | `predict(rst_n, enable, count)` | `ref_mem[addr]` 배열 |
| **비교 시점** | 매 트랜잭션 | Read 트랜잭션만 |
| **예측 방식** | 카운터 동작 시뮬레이션 | Write 시 메모리 업데이트, Read 시 비교 |
| **UVM 패턴** | `uvm_analysis_imp` + `write()` | **동일** |

### 11.6.3 실행 결과와 커버리지 확인

```
# 전체 레지스터 테스트 실행
vsim +UVM_TESTNAME=apb_full_test

UVM_INFO @ 0ns: reporter [RNTST] Running test apb_full_test...
UVM_INFO @ 20ns: uvm_test_top [apb_full_test] === 전체 레지스터 Write/Read 시작 ===

UVM_INFO @ 40ns: ... APB WRITE: addr=0x0, wdata=0x01
UVM_INFO @ 70ns: ... APB WRITE: addr=0x1, wdata=0x11
...
UVM_INFO @ 510ns: ... APB WRITE: addr=0xF, wdata=0xF1

UVM_INFO @ 540ns: ... APB READ: addr=0x0, rdata=0x01 ✓ MATCH
UVM_INFO @ 570ns: ... APB READ: addr=0x1, rdata=0x11 ✓ MATCH
...
UVM_INFO @ 1010ns: ... APB READ: addr=0xF, rdata=0xF1 ✓ MATCH

=== APB Scoreboard 결과 ===
  Write: 16건
  Read:  16건 (Match: 16, Error: 0)
  결과: PASS ✓
```

### 11.6.4 Part 2 → Part 3 구조 비교표

```
┌───────────────────────────────────────────────────────────┐
│          Part 2 → Part 3 구조 비교                        │
├───────────────────────────────────────────────────────────┤
│                                                           │
│   Part 2 (4비트 카운터)     Part 3 (APB Slave)           │
│                                                           │
│   counter_test              apb_write_read_test          │
│       │                         │                        │
│   counter_env               apb_env                      │
│       │                         │                        │
│   counter_agent             apb_agent                    │
│     ├─ counter_driver         ├─ apb_driver              │
│     ├─ counter_monitor        ├─ apb_monitor             │
│     └─ uvm_sequencer         └─ uvm_sequencer            │
│                                                           │
│   counter_scoreboard        apb_scoreboard               │
│     predict() 함수            ref_mem[] 배열              │
│                                                           │
│   counter_if                apb_if                        │
│     3 신호                    9 신호                      │
│     직접 접근                 clocking block              │
│                               modport                    │
│                                                           │
│   ─── UVM 구조: 동일 ────────────────────────            │
│   ─── 바뀐 것: 인터페이스 + 프로토콜 로직만 ──          │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

> 💡 **핵심 교훈**: Part 2에서 6개 챕터에 걸쳐 배운 UVM 구조(test → env → agent → scoreboard)가 Part 3에서 **그대로** 적용됩니다. 새로 배워야 할 것은 프로토콜 인터페이스와 BFM 로직뿐입니다. 이것이 UVM 재사용성의 가치입니다.

---

## 11.7 체크포인트

> **이 절의 목표**: 이 챕터의 핵심 개념을 확인합니다.

### 11.7.1 셀프 체크

다음 질문에 답할 수 있으면 이 챕터의 핵심을 이해한 것입니다:

**1. Clocking block을 사용하는 가장 큰 장점은?** (11.2)

<details>
<summary>정답 확인</summary>
타이밍 안전한 신호 접근을 보장합니다. `@(posedge clk)` 대신 `@(vif.drv_cb)`로 동기화하면, 신호의 셋업/홀드 타이밍을 clocking block이 자동으로 관리합니다. 또한 `input`/`output` 방향을 명시하여 드라이버가 읽기 전용 신호를 구동하는 실수를 방지합니다.
</details>

**2. Modport의 역할은?** (11.2)

<details>
<summary>정답 확인</summary>
인터페이스 사용자별로 접근 권한을 분리합니다. `modport driver`는 `drv_cb` clocking block만 접근할 수 있고, `modport monitor`는 `mon_cb`만 접근할 수 있습니다. 이를 통해 모니터가 실수로 신호를 구동하는 것을 컴파일 타임에 방지합니다.
</details>

**3. APB Write 전송의 2 Phase를 설명하세요.** (11.1)

<details>
<summary>정답 확인</summary>
① Setup Phase: `psel=1, penable=0`으로 슬레이브를 선택하고, `pwrite`, `paddr`, `pwdata`를 설정합니다. ② Access Phase: `penable=1`로 전송을 활성화합니다. 슬레이브가 `pready=1`을 응답하면 전송이 완료됩니다. Write의 경우 슬레이브가 이 시점에 데이터를 저장합니다.
</details>

**4. BFM 패턴이 직접 신호 대입보다 유리한 점은?** (11.4)

<details>
<summary>정답 확인</summary>
프로토콜 행위를 task로 캡슐화하여 재사용성을 높입니다. `drive_transfer()` 하나에 APB 프로토콜 전체를 구현하면, 다양한 시퀀스에서 "무엇을 보낼까"만 결정하고 "어떻게 보낼까"는 BFM에 위임합니다. 프로토콜 사양이 변경되어도 BFM task만 수정하면 됩니다.
</details>

**5. `counter_agent`와 `apb_agent`의 UVM 구조적 차이점은?** (11.5)

<details>
<summary>정답 확인</summary>
UVM 구조에는 차이가 없습니다. 둘 다 `uvm_agent`를 상속하고, `build_phase`에서 드라이버/모니터/시퀀서를 생성하며, `connect_phase`에서 포트를 연결합니다. 바뀐 것은 내부 컴포넌트의 타입(`counter_driver` → `apb_driver`)과 프로토콜 로직뿐입니다.
</details>

**6. APB 스코어보드의 Reference Model은 어떻게 동작하나요?** (11.6)

<details>
<summary>정답 확인</summary>
내부에 `ref_mem[0:15]` 메모리 배열을 유지합니다. Write 트랜잭션을 수신하면 `ref_mem[addr] = wdata`로 업데이트합니다. Read 트랜잭션을 수신하면 `ref_mem[addr]`의 값과 DUT가 응답한 `rdata`를 비교합니다. 불일치 시 `UVM_ERROR`를 보고합니다.
</details>

### 11.7.2 연습문제

**연습 11-1 (기본)**: APB Random 시퀀스 작성

랜덤 주소에 랜덤 데이터를 쓰고 읽는 시퀀스를 작성하세요. `num_transactions` 파라미터로 반복 횟수를 설정할 수 있어야 합니다.

<details>
<summary>힌트</summary>

```systemverilog
class apb_random_seq extends uvm_sequence #(apb_seq_item);
  int num_transactions = 20;

  task body();
    for (int i = 0; i < num_transactions; i++) begin
      // Write: randomize()로 addr, data 생성
      // Read: 같은 addr에서 읽기
    end
  endtask
endclass
```
</details>

**연습 11-2 (중급)**: Wait State 처리 추가

DUT의 `pready`가 항상 1이 아닌 경우를 처리하도록 드라이버를 수정하세요. `pready`가 0이면 Access Phase를 연장해야 합니다.

<details>
<summary>힌트</summary>
`drive_transfer()` task에서 Access Phase 부분을 수정합니다. `penable=1` 후 `while(vif.drv_cb.pready !== 1'b1) @(vif.drv_cb);`로 대기합니다. 이미 코드에 포함되어 있으나, DUT 측에서 `pready`를 지연시키는 테스트를 추가해야 합니다.
</details>

**연습 11-3 (도전)**: APB Coverage 수집기 작성

Ch.8에서 배운 `uvm_subscriber` 패턴을 사용하여 APB 커버리지 수집기를 작성하세요. 다음 항목을 커버해야 합니다:
- `cp_write`: Write/Read 분포
- `cp_addr`: 접근된 주소 범위 (0~15)
- `cx_write_addr`: Write/Read × 주소 조합

<details>
<summary>힌트</summary>

```systemverilog
class apb_coverage extends uvm_subscriber #(apb_seq_item);
  covergroup apb_cg;
    cp_write: coverpoint item.write { bins wr = {1}; bins rd = {0}; }
    cp_addr:  coverpoint item.addr  { bins addrs[] = {[0:15]}; }
    cx_write_addr: cross cp_write, cp_addr;
  endgroup
  // write() 함수에서 apb_cg.sample() 호출
endclass
```
</details>

### 11.7.3 이 챕터에서 배운 것

이 챕터에서 구축한 APB 검증 환경의 전체 파일 구조를 정리합니다:

```
apb_verification/
├── rtl/
│   └── apb_slave_memory.sv    ← DUT (16 x 8-bit 레지스터)
├── tb/
│   ├── apb_if.sv              ← 인터페이스 (clocking block + modport)
│   ├── apb_seq_item.sv        ← 트랜잭션 (addr, data, write)
│   ├── apb_driver.sv          ← 드라이버 (BFM: drive_transfer)
│   ├── apb_monitor.sv         ← 모니터 (프로토콜 관찰)
│   ├── apb_agent.sv           ← 에이전트 (드라이버 + 모니터 + 시퀀서)
│   ├── apb_scoreboard.sv      ← 스코어보드 (ref_mem 모델)
│   ├── apb_env.sv             ← 환경 (에이전트 + 스코어보드)
│   ├── apb_base_test.sv       ← 베이스 테스트
│   ├── apb_sequences.sv       ← 시퀀스 (write, read, write_read, full)
│   └── tb_top.sv              ← 테스트벤치 top
└── sim/
    └── run.do                 ← 시뮬레이션 스크립트
```

이 구조는 Ch.5~10에서 만든 4비트 카운터 환경과 **파일 단위로 1:1 대응**됩니다. Part 3의 나머지 챕터에서도 이 APB 환경을 계속 확장해 나갑니다.

### 11.7.4 다음 장 미리보기

Chapter 12에서는 **레지스터 모델(RAL)**을 배웁니다. 이 챕터에서 구축한 APB 인터페이스 위에 UVM RAL(Register Abstraction Layer)을 올려, 레지스터의 필드별 접근, 자동 읽기/쓰기 테스트, 백도어 접근 등을 구현합니다. APB 에이전트가 RAL의 "다리" 역할을 하며, 레지스터 검증이 크게 자동화됩니다.

**Part 3 로드맵:**

| 챕터 | 주제 | 이 챕터와의 관계 |
|------|------|-----------------|
| **Ch.11** | 인터페이스와 BFM | ✅ 지금 여기! APB 에이전트 구축 |
| **Ch.12** | 레지스터 모델 (RAL) | APB 에이전트 위에 RAL 계층 추가 |
| **Ch.13** | 고급 시퀀스 | APB 시퀀스를 가상 시퀀스로 확장 |
| **Ch.14** | 검증 자동화 | APB 환경에 자동화 인프라 구축 |
| **Ch.15** | 프로젝트 종합 | 전체 검증 환경 통합 및 리뷰 |

> 💡 **핵심 메시지**: 이 챕터에서 만든 APB 에이전트와 검증 환경이 Part 3 전체의 **기반**이 됩니다. 각 챕터에서 새로운 UVM 기능을 하나씩 추가하며, 실무 수준의 검증 환경을 완성해 나갑니다.
