# Chapter 14: 검증 자동화

> **학습 목표**
> - **기능 커버리지(Functional Coverage)**의 개념과 covergroup/coverpoint/cross를 구현할 수 있다
> - **UVM 커버리지 컬렉터**를 `uvm_subscriber`로 작성하여 환경에 통합할 수 있다
> - **SVA(SystemVerilog Assertion)**로 APB 프로토콜 규칙을 자동 검사할 수 있다
> - **커버리지 클로저(Coverage Closure)** 전략을 이해하고 적용할 수 있다
> - Ch.11~13에서 만든 APB 검증 환경에 커버리지와 어서션을 추가하여 **완전한 검증 인프라**를 구축할 수 있다

> **선수 지식**: Chapter 8의 analysis port(커버리지 데이터 수집 경로)와 Chapter 11의 APB 에이전트(커버리지/어서션 대상)가 핵심 기반입니다.

---

## 14.1 왜 검증 자동화가 필요한가

> **이 절의 목표**: 커버리지와 어서션의 필요성을 이해하고, 검증 자동화의 전체 그림을 파악합니다.

### 14.1.1 "검증이 충분한가?" — 커버리지의 필요성

Ch.11~13에서 APB 검증 환경을 만들었습니다. 드라이버가 트랜잭션을 보내고, 모니터가 관찰하고, 스코어보드가 비교합니다. 하지만 중요한 질문이 남습니다:

> **"테스트가 모든 시나리오를 검증했는가?"**

| 질문 | 대답할 수 없는 이유 |
|------|---------------------|
| 모든 주소(0x0~0xF)에 쓰기를 했는가? | 테스트 로그를 하나하나 확인해야 함 |
| 읽기와 쓰기가 골고루 실행되었는가? | 랜덤 테스트라 보장 불가 |
| 연속 쓰기 후 읽기 패턴이 테스트되었는가? | 시나리오 조합 추적 불가 |
| 모든 레지스터 필드 값이 검증되었는가? | 수동 추적 비현실적 |

**커버리지(Coverage)**는 이 질문에 자동으로 답합니다. **"무엇을 검증했고, 무엇을 아직 검증하지 못했는지"**를 수치로 보여줍니다.

> 💡 **비유**: 시험공부를 할 때 **체크리스트**를 만드는 것과 같습니다. "1장 ✅, 2장 ✅, 3장 ❌, 4장 ✅" — 3장을 아직 공부하지 않았음을 즉시 알 수 있습니다. 커버리지는 검증의 체크리스트입니다.

### 14.1.2 "프로토콜을 위반했는가?" — 어서션의 필요성

스코어보드는 **데이터 정확성**만 검증합니다. 하지만 프로토콜 **타이밍 규칙**은 검증하지 않습니다:

```systemverilog
// 스코어보드가 검증하는 것:
// "주소 0x5에 쓴 값 0xAB가 읽을 때도 0xAB인가?" → 데이터 무결성

// 스코어보드가 검증하지 못하는 것:
// "psel이 1인데 penable이 2사이클 후에 올라갔다" → 프로토콜 위반!
// "penable이 올라갔는데 pready 없이 3사이클 유지됐다" → 타이밍 위반!
```

**어서션(Assertion)**은 **"이 조건이 항상 참이어야 한다"**를 선언하고, 위반 시 즉시 알려줍니다.

> 💡 **비유**: 도로에 설치된 **과속 CCTV**와 같습니다. 운전자가 규칙을 지키는지 24시간 자동 감시합니다. 어서션은 프로토콜 규칙의 CCTV입니다.

**커버리지와 어서션의 역할 비교:**

| 구분 | 커버리지 | 어서션 |
|------|---------|--------|
| **질문** | "무엇을 검증했는가?" | "규칙을 위반했는가?" |
| **동작** | 수동적 (관찰·기록) | 능동적 (감시·알림) |
| **결과** | 백분율 (85% 달성) | Pass/Fail (위반 발생!) |
| **비유** | 시험 체크리스트 | 과속 CCTV |
| **위치** | 모니터 뒤 (analysis port) | 인터페이스 (신호 레벨) |

### 14.1.3 검증 자동화 아키텍처

커버리지와 어서션이 검증 환경의 어디에 위치하는지 봅시다:

```
검증 자동화 아키텍처

┌─────────────────────────────────────────────┐
│  UVM Test                                   │
│  ┌──────────────────────────────────┐       │
│  │  Environment                     │       │
│  │  ┌─────────┐  ┌──────────────┐  │       │
│  │  │  Agent   │  │ Coverage     │  │       │
│  │  │ ┌─────┐  │  │ Collector    │  │       │
│  │  │ │ Drv │  │  │ (covergroup) │  │       │
│  │  │ ├─────┤  │  └──────┬───────┘  │       │
│  │  │ │ Mon │──┼─────────┘ ap       │       │
│  │  │ ├─────┤  │  ┌──────────────┐  │       │
│  │  │ │ Sqr │  │  │ Scoreboard   │  │       │
│  │  │ └─────┘  │  └──────────────┘  │       │
│  │  └─────────┘                     │       │
│  └──────────────────────────────────┘       │
└───────────────────┬─────────────────────────┘
                    │
┌───────────────────▼─────────────────────────┐
│  DUT (APB Slave Memory)                     │
│  ┌──────────────────────────────────┐       │
│  │  Assertion Module (SVA)          │       │
│  │  • psel → penable 규칙          │       │
│  │  • pready 타이밍 규칙            │       │
│  │  • pwrite 안정성 규칙            │       │
│  └──────────────────────────────────┘       │
└─────────────────────────────────────────────┘
```

**핵심 위치:**
- **커버리지 컬렉터**: 환경 안, 모니터의 analysis port에 연결 (Ch.8 스코어보드와 같은 패턴)
- **어서션 모듈**: DUT 근처, 인터페이스 신호를 직접 관찰

---

## 14.2 기능 커버리지 기초

> **이 절의 목표**: covergroup, coverpoint, bins, cross의 기본 문법과 동작을 이해합니다.

### 14.2.1 covergroup과 coverpoint

**covergroup**은 커버리지를 수집하는 컨테이너입니다. **coverpoint**는 관찰할 변수를 지정합니다.

```systemverilog
// ============================================================
// 기능 커버리지 기초: covergroup과 coverpoint
// ============================================================
class apb_coverage_basic;

  // 관찰 대상 변수
  bit [3:0] addr;
  bit       write;
  bit [7:0] data;

  // covergroup 정의 — "무엇을 관찰할지" 선언
  covergroup apb_cg;
    // coverpoint: 관찰할 변수 지정
    cp_addr:  coverpoint addr;   // 주소 (0x0~0xF)
    cp_write: coverpoint write;  // 읽기/쓰기
    cp_data:  coverpoint data;   // 데이터 (0x00~0xFF)
  endgroup

  function new();
    apb_cg = new();  // covergroup 인스턴스 생성 — 필수!
  endfunction

  // sample: 값을 기록
  function void sample(bit [3:0] a, bit w, bit [7:0] d);
    addr  = a;
    write = w;
    data  = d;
    apb_cg.sample();  // ★ 현재 값을 기록
  endfunction

endclass
```

**동작 원리:**

| 단계 | 동작 | 결과 |
|------|------|------|
| 1. `new()` | covergroup 인스턴스 생성 | 빈 체크리스트 생성 |
| 2. 변수 할당 | `addr = 4'h3; write = 1;` | 관찰 대상 업데이트 |
| 3. `sample()` | 현재 값을 기록 | 체크리스트에 ✅ 표시 |
| 4. 반복 | 다양한 값으로 반복 | 점점 더 많은 항목 ✅ |
| 5. 리포트 | 커버리지 비율 확인 | "addr: 87.5%, write: 100%" |

### 14.2.2 bins — 값 분류하기

기본 coverpoint는 가능한 모든 값에 대해 자동으로 bin을 생성합니다. `cp_data`는 256개 bin이 생깁니다. **bins**로 의미 있는 그룹으로 분류할 수 있습니다.

```systemverilog
// ============================================================
// bins: 값을 의미 있는 그룹으로 분류
// ============================================================
covergroup apb_cg_with_bins;

  // 주소: 특수 레지스터와 일반 레지스터 분류
  cp_addr: coverpoint addr {
    bins ctrl_reg    = {4'h0};           // ctrl_reg 주소
    bins status_reg  = {4'h1};           // status_reg 주소
    bins data_reg    = {4'h2};           // data_reg 주소
    bins general[]   = {[4'h3:4'hF]};   // 일반 레지스터 (13개 bin)
  }

  // 읽기/쓰기: 명시적 이름
  cp_write: coverpoint write {
    bins read  = {0};
    bins write = {1};
  }

  // 데이터: 범위별 분류
  cp_data: coverpoint data {
    bins zero     = {8'h00};             // 제로 값
    bins low      = {[8'h01:8'h7F]};     // 하위 범위
    bins high     = {[8'h80:8'hFE]};     // 상위 범위
    bins all_ones = {8'hFF};             // 올원 값
  }

  // 전이(transition): 읽기→쓰기→읽기 패턴 감지
  cp_write_trans: coverpoint write {
    bins read_write   = (0 => 1);    // 읽기 후 쓰기
    bins write_read   = (1 => 0);    // 쓰기 후 읽기
    bins write_write  = (1 => 1);    // 연속 쓰기
    bins read_read    = (0 => 0);    // 연속 읽기
  }

  // 잘못된 접근은 수집하지 않음
  cp_addr_illegal: coverpoint addr {
    illegal_bins reserved = {4'hF};  // 예약 주소 → 발생하면 에러!
  }

endgroup
```

**bins 종류:**

| 종류 | 문법 | 동작 |
|------|------|------|
| **명시적 bins** | `bins name = {값};` | 특정 값을 추적 |
| **범위 bins** | `bins name = {[min:max]};` | 범위 내 값을 하나의 bin으로 |
| **배열 bins** | `bins name[] = {[min:max]};` | 범위 내 값을 개별 bin으로 |
| **전이 bins** | `bins name = (a => b);` | 값 변화 패턴 추적 |
| **illegal_bins** | `illegal_bins name = {값};` | 발생하면 에러 보고 |
| **ignore_bins** | `ignore_bins name = {값};` | 수집에서 제외 |

### 14.2.3 cross — 교차 커버리지

**cross**는 두 coverpoint의 **조합**을 추적합니다. "주소 0x0에 쓰기"와 "주소 0x0에 읽기"를 구분할 수 있습니다.

```systemverilog
// ============================================================
// cross: 교차 커버리지
// ============================================================
covergroup apb_cross_cg;

  cp_addr: coverpoint addr {
    bins ctrl   = {4'h0};
    bins status = {4'h1};
    bins data   = {4'h2};
  }

  cp_write: coverpoint write {
    bins read  = {0};
    bins write = {1};
  }

  cp_data: coverpoint data {
    bins zero     = {8'h00};
    bins non_zero = {[8'h01:8'hFF]};
  }

  // ★ 교차 커버리지: addr × write
  // → ctrl+read, ctrl+write, status+read, status+write, data+read, data+write
  cx_addr_write: cross cp_addr, cp_write;

  // ★ 교차 커버리지: addr × write × data (3차원)
  // → ctrl+write+zero, ctrl+write+non_zero, ...
  cx_all: cross cp_addr, cp_write, cp_data;

endgroup
```

**cross의 위력:**

| coverpoint만 | cross |
|---------------|-------|
| addr: ctrl ✅, status ✅ | ctrl+read ✅, ctrl+write ✅ |
| write: read ✅, write ✅ | status+read ❌, status+write ✅ |
| (조합 추적 불가) | → status_reg에 읽기를 안 했다! |

### 14.2.4 커버리지 옵션과 리포트

```systemverilog
// ============================================================
// 커버리지 옵션 설정
// ============================================================
covergroup apb_full_cg with function sample(bit [3:0] a, bit w, bit [7:0] d);

  // ---- 옵션 ----
  option.per_instance = 1;    // 인스턴스별 커버리지 추적
  option.goal = 95;           // 목표: 95% (100%가 아님!)
  option.name = "APB_Coverage";
  option.comment = "APB transaction coverage";
  option.at_least = 5;        // 각 bin 최소 5회 히트 필요
  option.weight = 1;          // 전체 커버리지 계산 시 가중치

  cp_addr: coverpoint a {
    bins regs[] = {[0:15]};
    option.auto_bin_max = 16;  // 최대 자동 bin 수
  }

  cp_write: coverpoint w {
    bins read  = {0};
    bins write = {1};
  }

  cp_data: coverpoint d {
    bins zero     = {8'h00};
    bins low      = {[8'h01:8'h7F]};
    bins high     = {[8'h80:8'hFE]};
    bins all_ones = {8'hFF};
  }

  cx_addr_dir: cross cp_addr, cp_write;

endgroup
```

> ⚠️ **왜 목표가 100%가 아닌가?** 실무에서 100% 기능 커버리지는 비현실적이거나 불필요할 수 있습니다. 예를 들어, 읽기 전용 레지스터에 쓰기 조합은 의미가 없습니다. 보통 **90~95%**를 목표로 하고, 나머지는 `ignore_bins`로 제외하거나 합리적인 사유를 문서화합니다.

> 🔧 **트러블슈팅**: 커버리지 관련 오류:

| 오류 | 원인 | 해결 |
|------|------|------|
| `Covergroup not sampled` | `sample()` 호출 누락 | `write()` 또는 이벤트에서 `cg.sample()` 호출 |
| 커버리지 항상 0% | covergroup `new()` 누락 | 생성자에서 `cg = new()` 확인 |
| 너무 많은 bin (메모리 부족) | auto_bin_max가 큼 | `option.auto_bin_max` 조절 또는 명시적 bins 사용 |

---

## 14.3 APB 커버리지 모델

> **이 절의 목표**: Ch.11의 APB 에이전트에 UVM 커버리지 컬렉터를 추가합니다.

### 14.3.1 APB 트랜잭션 커버리지 설계

APB 트랜잭션에서 무엇을 커버해야 할까요?

| 커버리지 항목 | coverpoint | bins |
|---------------|------------|------|
| 주소 범위 | `cp_addr` | ctrl(0), status(1), data(2), general(3~15) |
| 읽기/쓰기 방향 | `cp_write` | read, write |
| 데이터 경계값 | `cp_data` | zero(0x00), low, high, all_ones(0xFF) |
| 전이 패턴 | `cp_trans` | read→write, write→read, write→write |
| 주소×방향 교차 | `cx_addr_dir` | 모든 주소에 읽기/쓰기 수행 확인 |

### 14.3.2 UVM 커버리지 컬렉터 구현

```systemverilog
// ============================================================
// APB 커버리지 컬렉터 — uvm_subscriber 상속
// ============================================================
class apb_coverage_collector extends uvm_subscriber#(apb_seq_item);
  `uvm_component_utils(apb_coverage_collector)

  // ---- 커버리지 변수 ----
  bit [3:0] addr;
  bit       write_flag;
  bit [7:0] data;

  // ---- covergroup 정의 ----
  covergroup apb_cg;
    option.per_instance = 1;
    option.goal = 95;

    // 주소 커버리지
    cp_addr: coverpoint addr {
      bins ctrl_reg    = {4'h0};
      bins status_reg  = {4'h1};
      bins data_reg    = {4'h2};
      bins general[]   = {[4'h3:4'hF]};
    }

    // 방향 커버리지
    cp_write: coverpoint write_flag {
      bins read  = {0};
      bins write = {1};
    }

    // 데이터 커버리지
    cp_data: coverpoint data {
      bins zero     = {8'h00};
      bins low      = {[8'h01:8'h7F]};
      bins high     = {[8'h80:8'hFE]};
      bins all_ones = {8'hFF};
    }

    // 전이 커버리지
    cp_write_trans: coverpoint write_flag {
      bins read_after_write  = (1 => 0);
      bins write_after_read  = (0 => 1);
      bins consecutive_write = (1 => 1);
      bins consecutive_read  = (0 => 0);
    }

    // 교차 커버리지: 주소 × 방향
    cx_addr_dir: cross cp_addr, cp_write;

    // 교차 커버리지: 방향 × 데이터
    cx_dir_data: cross cp_write, cp_data;
  endgroup

  function new(string name, uvm_component parent);
    super.new(name, parent);
    apb_cg = new();  // ★ covergroup 인스턴스 생성 필수!
  endfunction

  // ★ write() — analysis port에서 트랜잭션 수신 시 자동 호출
  virtual function void write(apb_seq_item t);
    // 변수 업데이트
    addr       = t.paddr;
    write_flag = t.pwrite;
    data       = t.pwrite ? t.pwdata : t.prdata;

    // 커버리지 샘플
    apb_cg.sample();

    `uvm_info(get_type_name(), $sformatf("Coverage sampled: addr=0x%0h %s data=0x%02h",
              addr, write_flag ? "WR" : "RD", data), UVM_HIGH)
  endfunction

  // ---- 시뮬레이션 종료 시 커버리지 리포트 ----
  function void report_phase(uvm_phase phase);
    `uvm_info(get_type_name(), $sformatf(
      "\n=== APB Coverage Report ===\n  Overall: %.1f%%\n  addr:    %.1f%%\n  write:   %.1f%%\n  data:    %.1f%%\n  addr×dir: %.1f%%\n===========================",
      apb_cg.get_coverage(),
      apb_cg.cp_addr.get_coverage(),
      apb_cg.cp_write.get_coverage(),
      apb_cg.cp_data.get_coverage(),
      apb_cg.cx_addr_dir.get_coverage()
    ), UVM_LOW)
  endfunction
endclass
```

**핵심 패턴**: `uvm_subscriber#(apb_seq_item)` → `write(apb_seq_item t)` → `apb_cg.sample()`

이 패턴은 Ch.8의 스코어보드와 동일합니다. 모니터의 analysis port에 연결하면, 모든 트랜잭션이 자동으로 커버리지에 기록됩니다.

### 14.3.3 환경에 커버리지 컬렉터 통합

```systemverilog
// ============================================================
// 커버리지 컬렉터를 환경에 추가
// ============================================================
class apb_coverage_env extends uvm_env;
  `uvm_component_utils(apb_coverage_env)

  apb_agent                   apb_agt;
  apb_coverage_collector      cov_col;   // ★ 커버리지 컬렉터

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    apb_agt = apb_agent::type_id::create("apb_agt", this);
    cov_col = apb_coverage_collector::type_id::create("cov_col", this);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    // ★ 모니터의 analysis port → 커버리지 컬렉터 연결
    apb_agt.mon.ap.connect(cov_col.analysis_export);
  endfunction
endclass
```

**연결 구조:**

```
Monitor → analysis_port → Coverage Collector (write → sample)
                        → Scoreboard        (write → compare)
```

모니터의 하나의 analysis port에 **여러 구독자**를 연결할 수 있습니다. 커버리지 컬렉터와 스코어보드가 동시에 같은 트랜잭션을 수신합니다.

**`write()` 자동 호출 흐름:**

| 단계 | 컴포넌트 | 동작 |
|------|---------|------|
| 1 | **드라이버** | APB 트랜잭션을 DUT에 전송 |
| 2 | **모니터** | 인터페이스에서 트랜잭션을 관찰 |
| 3 | **모니터** | `ap.write(observed_txn)` 호출 |
| 4 | **커버리지 컬렉터** | `write(t)` 자동 호출 (analysis port 연결) |
| 5 | **커버리지 컬렉터** | 변수 업데이트 → `apb_cg.sample()` |
| 6 | **covergroup** | 현재 값을 bins에 기록 |

> 💡 `write()` 메서드는 프로그래머가 직접 호출하지 않습니다. 모니터의 `ap.write()`가 호출되면, 연결된 모든 subscriber의 `write()`가 **자동으로** 호출됩니다. 이것이 Ch.8에서 배운 analysis port의 **발행-구독(pub-sub) 패턴**입니다.

---

## 14.4 SystemVerilog 어서션 (SVA)

> **이 절의 목표**: 즉시 어서션과 동시 어서션의 문법을 이해하고 작성합니다.

### 14.4.1 즉시 어서션 (Immediate Assertion)

즉시 어서션은 **조합 논리** 검사에 사용합니다. `if`문처럼 조건을 즉시 검사합니다.

```systemverilog
// ============================================================
// 즉시 어서션: 조건을 즉시 검사
// ============================================================

// 기본 문법
assert (condition)
  /* pass action */;
else
  /* fail action */;

// 예: APB 데이터 무결성 검사
always @(posedge clk) begin
  if (psel && penable && pready && !pwrite) begin
    // 읽기 완료 시: 데이터가 X가 아닌지 검사
    assert (prdata !== 8'hxx)
      // Pass: 아무것도 안 함
    else
      $error("APB Read returned X at addr=0x%0h", paddr);
  end
end
```

**3가지 심각도:**

| 키워드 | 심각도 | 동작 |
|--------|--------|------|
| `$info(...)` | 정보 | 로그만 출력 |
| `$warning(...)` | 경고 | 경고 출력 |
| `$error(...)` | 오류 | 오류 출력 (시뮬레이션 계속) |
| `$fatal(...)` | 치명적 | 시뮬레이션 종료 |

### 14.4.2 동시 어서션 (Concurrent Assertion)

동시 어서션은 **시간 관계**를 검사합니다. 클록 에지 기반으로 여러 사이클에 걸친 규칙을 표현합니다.

```systemverilog
// ============================================================
// 동시 어서션: 시간에 걸친 규칙 검사
// ============================================================

// 기본 문법: property + assert
property p_name;
  @(posedge clk) disable iff (!resetn)
  antecedent |-> consequent;  // "선행조건이면 → 결과 참"
endproperty

assert property (p_name)
else $error("Property violated!");

// 예: psel이 올라가면, 다음 사이클에 penable이 올라가야 한다
property p_psel_penable;
  @(posedge clk) disable iff (!presetn)
  (psel && !penable) |=> penable;  // |=> : 다음 사이클에
endproperty

assert property (p_psel_penable)
else $error("APB: penable did not rise one cycle after psel!");
```

**`|->` vs `|=>`:**

| 연산자 | 이름 | 동작 | 타이밍 |
|--------|------|------|--------|
| `\|->` | 겹침 함축 (Overlapping) | 같은 사이클에서 결과 검사 | `A \|-> B` = A가 참이면 **같은 사이클**에 B도 참 |
| `\|=>` | 비겹침 함축 (Non-overlapping) | 다음 사이클에서 결과 검사 | `A \|=> B` = A가 참이면 **다음 사이클**에 B가 참 |

```
|-> 겹침 (같은 사이클):     |=> 비겹침 (다음 사이클):

  clk:  ┌──┐  ┌──┐           clk:  ┌──┐  ┌──┐
        │  │  │  │                 │  │  │  │
  A:  ──┤1 ├──┤  ├──         A:  ──┤1 ├──┤  ├──
  B:  ──┤1 ├──┤  ├──         B:  ──┤  ├──┤1 ├──
        같은 사이클에 B=1          다음 사이클에 B=1
```

**APB 프로토콜에서의 `|->` vs `|=>` 실전 예시:**

```systemverilog
// |-> 예: psel=1이면 같은 사이클에 paddr가 안정해야 한다
property p_addr_valid_when_sel;
  @(posedge clk) disable iff (!presetn)
  psel |-> !$isunknown(paddr);  // psel과 같은 사이클에 paddr 유효
endproperty

// |=> 예: Setup Phase 후 다음 사이클에 Access Phase
property p_setup_then_access;
  @(posedge clk) disable iff (!presetn)
  (psel && !penable) |=> (psel && penable);  // 다음 사이클에 penable=1
endproperty

// 사이클별 동작:
// clk:     ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐
// psel:    0   1   1   0   0     ← 사이클 1~2 활성
// penable: 0   0   1   0   0     ← 사이클 2에 올라감
// paddr:   X  0x3 0x3  X   X     ← psel=1일 때 유효 (|->)
//              ↑   ↑
//           Setup Access          ← Setup |=> Access (|=>)
```

### 14.4.3 시퀀스와 프로퍼티

**시퀀스(sequence)**는 여러 사이클에 걸친 신호 패턴을 정의합니다. **프로퍼티(property)**는 시퀀스를 조합하여 검증 규칙을 만듭니다.

```systemverilog
// ============================================================
// 시퀀스와 프로퍼티
// ============================================================

// 시퀀스: APB Setup Phase → Access Phase 패턴
sequence s_apb_setup;
  psel && !penable;  // Setup Phase: psel=1, penable=0
endsequence

sequence s_apb_access;
  psel && penable;   // Access Phase: psel=1, penable=1
endsequence

// 프로퍼티: Setup 후 다음 사이클에 Access
property p_apb_handshake;
  @(posedge clk) disable iff (!presetn)
  s_apb_setup |=> s_apb_access;
endproperty

// 프로퍼티: Access Phase에서 pready가 오면 다음 사이클에 psel 해제 또는 새 Setup
property p_apb_complete;
  @(posedge clk) disable iff (!presetn)
  (psel && penable && pready) |=> (!penable);
endproperty

// 어서션 인스턴스화
assert_apb_handshake: assert property (p_apb_handshake)
else $error("APB: Setup→Access handshake violated!");

assert_apb_complete: assert property (p_apb_complete)
else $error("APB: Transfer completion violated!");
```

**시퀀스에서 사용하는 시간 연산자:**

| 연산자 | 의미 | 예시 |
|--------|------|------|
| `##1` | 1사이클 후 | `a ##1 b` = a 후 1사이클에 b |
| `##[1:3]` | 1~3사이클 후 | `a ##[1:3] b` = a 후 1~3사이클 내에 b |
| `##0` | 같은 사이클 | `a ##0 b` = a와 b 동시에 |
| `[*3]` | 3회 반복 | `a[*3]` = a가 3사이클 연속 |
| `[*1:5]` | 1~5회 반복 | `a[*1:5]` = a가 1~5사이클 연속 |

> 🔧 **트러블슈팅**: 어서션 관련 오류:

| 오류 | 원인 | 해결 |
|------|------|------|
| 리셋 중 어서션 실패 | `disable iff` 누락 | `disable iff (!resetn)` 추가 |
| 시뮬레이션 시작 시 실패 | 초기 X 값 | `$isunknown()` 검사 추가 또는 리셋 후 활성화 |
| 어서션이 절대 트리거 안 됨 | 선행조건이 항상 거짓 | `cover property`로 선행조건 발생 확인 |

---

## 14.5 APB 프로토콜 어서션

> **이 절의 목표**: APB 프로토콜 규칙을 SVA로 구현하고 환경에 연결합니다.

### 14.5.1 APB 프로토콜 규칙 정리

AMBA 3.0 APB 스펙에서 가장 중요한 규칙들:

| 규칙 | 설명 | SVA로 검증 |
|------|------|------------|
| **R1** | psel=1 후 다음 사이클에 penable=1 | `psel && !penable \|=> penable` |
| **R2** | penable은 1사이클만 활성 | `penable \|=> !penable` (pready 시) |
| **R3** | pwrite는 전송 중 안정 유지 | `psel \|-> ##1 (pwrite == $past(pwrite))` |
| **R4** | paddr는 전송 중 안정 유지 | `psel \|-> ##1 (paddr == $past(paddr))` |
| **R5** | pwdata는 쓰기 전송 중 안정 | `(psel && pwrite) \|-> ##1 (pwdata == $past(pwdata))` |

### 14.5.2 어서션 모듈 구현

```systemverilog
// ============================================================
// APB 프로토콜 어서션 모듈
// ============================================================
module apb_protocol_assertions (
  input logic        clk,
  input logic        resetn,
  input logic        psel,
  input logic        penable,
  input logic        pwrite,
  input logic [3:0]  paddr,
  input logic [7:0]  pwdata,
  input logic [7:0]  prdata,
  input logic        pready
);

  // ================================================================
  // R1: Setup → Access 핸드셰이크
  // psel이 올라가고 penable이 내려가 있으면 (Setup Phase),
  // 다음 사이클에 penable이 올라가야 한다 (Access Phase)
  // ================================================================
  property p_setup_to_access;
    @(posedge clk) disable iff (!resetn)
    (psel && !penable) |=> (psel && penable);
  endproperty

  assert_setup_access: assert property (p_setup_to_access)
  else $error("[APB-R1] Setup→Access handshake violated! Time=%0t", $time);

  // ================================================================
  // R2: 전송 완료 후 penable 해제
  // pready가 오면 전송 완료. 다음 사이클에 penable이 내려가야 한다
  // ================================================================
  property p_transfer_complete;
    @(posedge clk) disable iff (!resetn)
    (psel && penable && pready) |=> (!penable);
  endproperty

  assert_transfer_complete: assert property (p_transfer_complete)
  else $error("[APB-R2] penable not deasserted after transfer! Time=%0t", $time);

  // ================================================================
  // R3: pwrite 안정성
  // 전송 중(psel=1) pwrite는 변하면 안 된다
  // ================================================================
  property p_pwrite_stable;
    @(posedge clk) disable iff (!resetn)
    (psel && !penable) |=> (pwrite == $past(pwrite));
  endproperty

  assert_pwrite_stable: assert property (p_pwrite_stable)
  else $error("[APB-R3] pwrite changed during transfer! Time=%0t", $time);

  // ================================================================
  // R4: paddr 안정성
  // 전송 중(psel=1) paddr는 변하면 안 된다
  // ================================================================
  property p_paddr_stable;
    @(posedge clk) disable iff (!resetn)
    (psel && !penable) |=> (paddr == $past(paddr));
  endproperty

  assert_paddr_stable: assert property (p_paddr_stable)
  else $error("[APB-R4] paddr changed during transfer! Time=%0t", $time);

  // ================================================================
  // R5: pwdata 안정성 (쓰기 시)
  // 쓰기 전송 중 pwdata는 변하면 안 된다
  // ================================================================
  property p_pwdata_stable;
    @(posedge clk) disable iff (!resetn)
    (psel && !penable && pwrite) |=> (pwdata == $past(pwdata));
  endproperty

  assert_pwdata_stable: assert property (p_pwdata_stable)
  else $error("[APB-R5] pwdata changed during write transfer! Time=%0t", $time);

  // ================================================================
  // 커버 프로퍼티: 어서션이 실제로 트리거되었는지 확인
  // ================================================================
  cover_setup:    cover property (@(posedge clk) psel && !penable);
  cover_access:   cover property (@(posedge clk) psel && penable);
  cover_write:    cover property (@(posedge clk) psel && penable && pready && pwrite);
  cover_read:     cover property (@(posedge clk) psel && penable && pready && !pwrite);

endmodule
```

### 14.5.3 어서션과 환경 연결

어서션 모듈을 테스트벤치 최상위에서 바인드합니다:

```systemverilog
// ============================================================
// 테스트벤치 최상위: 어서션 모듈 바인드
// ============================================================
module tb_top;

  // 클록/리셋
  logic clk, resetn;

  // APB 인터페이스
  apb_if apb_vif(clk, resetn);

  // DUT
  apb_slave_memory dut (
    .clk     (clk),
    .resetn  (resetn),
    .psel    (apb_vif.psel),
    .penable (apb_vif.penable),
    .pwrite  (apb_vif.pwrite),
    .paddr   (apb_vif.paddr),
    .pwdata  (apb_vif.pwdata),
    .prdata  (apb_vif.prdata),
    .pready  (apb_vif.pready)
  );

  // ★ 어서션 모듈 바인드 — DUT 신호를 직접 관찰
  apb_protocol_assertions apb_assert (
    .clk     (clk),
    .resetn  (resetn),
    .psel    (apb_vif.psel),
    .penable (apb_vif.penable),
    .pwrite  (apb_vif.pwrite),
    .paddr   (apb_vif.paddr),
    .pwdata  (apb_vif.pwdata),
    .prdata  (apb_vif.prdata),
    .pready  (apb_vif.pready)
  );

  // 클록 생성
  initial clk = 0;
  always #5 clk = ~clk;

  // UVM 시작
  initial begin
    uvm_config_db#(virtual apb_if)::set(null, "*", "vif", apb_vif);
    run_test();
  end

endmodule
```

> 💡 **`bind` 문법 대안**: 어서션을 DUT 내부에 바인드할 수도 있습니다:
> ```systemverilog
> bind apb_slave_memory apb_protocol_assertions assert_inst (.*);
> ```
> 이 방법은 DUT 코드를 수정하지 않고 어서션을 추가할 수 있어 실무에서 선호됩니다.

---

## 14.6 커버리지 클로저 전략

> **이 절의 목표**: 커버리지 리포트를 분석하고, 미달 항목을 보완하는 전략을 학습합니다.

### 14.6.1 커버리지 리포트 분석

시뮬레이션 후 커버리지 리포트 예시:

```
=== APB Coverage Report ===
  Overall:   72.3%
  addr:      87.5%  (14/16 bins hit)
  write:    100.0%  (2/2 bins hit)
  data:      75.0%  (3/4 bins hit)
  addr×dir:  68.8%  (22/32 bins hit)
===========================

Missing bins:
  addr:     general[14], general[15]    ← 주소 0xE, 0xF 미접근
  data:     all_ones                    ← 0xFF 데이터 미생성
  addr×dir: ctrl+read, status+write,   ← 특정 조합 미실행
            general[14]+read, ...
```

**분석:**
1. `addr`: 주소 0xE, 0xF에 접근하지 않음 → 시퀀스에 해당 주소 추가
2. `data`: 0xFF 경계값 미생성 → constraint에 경계값 포함
3. `addr×dir`: 특정 조합 미실행 → 타겟 시퀀스 작성

**리포트 → 분석 → 타겟 시퀀스: 한 눈에 보는 연결 흐름**

실무에서 커버리지 클로저는 아래의 3단계를 **반복**합니다. 위 리포트를 예시로 전체 과정을 연결해 봅시다:

```
[Step 1] 리포트에서 갭 식별
─────────────────────────────
  addr×dir:  68.8%  ← 목표 95% 미달!
  Missing: general[14]+read, general[14]+write,
           general[15]+read, general[15]+write,
           ctrl+read, status+write ...

          ↓ (어떤 조합이 빠졌는지 정리)

[Step 2] 갭 분석 및 원인 파악
─────────────────────────────
  갭 1: addr 0xE, 0xF 미접근
    → 원인: 랜덤 시퀀스의 addr 범위가 0x0~0xD에 집중
    → 해결: addr == 4'hE, 4'hF를 강제하는 시퀀스

  갭 2: data 0xFF 미생성
    → 원인: 랜덤 분포에서 경계값(all_ones) 확률 낮음
    → 해결: pwdata == 8'hFF를 constraint로 지정

  갭 3: ctrl+read, status+write 조합 미실행
    → 원인: 특정 주소+방향 조합이 랜덤으로 발생하지 않음
    → 해결: 해당 조합을 명시적으로 실행하는 시퀀스

          ↓ (분석 결과를 코드로 변환)

[Step 3] 타겟 시퀀스 작성
─────────────────────────────
  apb_coverage_target_seq:
    - Gap 1 해결: addr 4'hE, 4'hF에 read/write 실행
    - Gap 2 해결: pwdata == 8'hFF로 write 실행
    - Gap 3 해결: addr 0x0 read, addr 0x1 write 실행
```

> 💡 **핵심 원칙**: 랜덤 테스트가 **넓은 범위**를 커버하고, 타겟 시퀀스가 **남은 구멍**을 메웁니다. 이 두 가지를 조합하는 것이 커버리지 클로저의 핵심 전략입니다.

**테스트 실행 순서 — 실무 권장:**

```systemverilog
// ============================================================
// 커버리지 클로저를 위한 테스트 실행 전략
// ============================================================
class apb_coverage_closure_test extends uvm_test;
  `uvm_component_utils(apb_coverage_closure_test)

  // ... 생성자, 환경 생략 ...

  virtual task run_phase(uvm_phase phase);
    apb_random_seq      rand_seq;   // 1단계: 랜덤 (넓은 커버리지)
    apb_coverage_target_seq target_seq; // 2단계: 타겟 (갭 채우기)

    phase.raise_objection(this);

    // ── 1단계: 랜덤 시퀀스로 기본 커버리지 확보 ──
    rand_seq = apb_random_seq::type_id::create("rand_seq");
    rand_seq.start(env.agent.sequencer);
    `uvm_info("TEST", $sformatf("랜덤 후 커버리지: %.1f%%",
              $get_coverage()), UVM_LOW)

    // ── 2단계: 타겟 시퀀스로 남은 갭 채우기 ──
    target_seq = apb_coverage_target_seq::type_id::create("target_seq");
    target_seq.start(env.agent.sequencer);
    `uvm_info("TEST", $sformatf("타겟 후 커버리지: %.1f%%",
              $get_coverage()), UVM_LOW)

    phase.drop_objection(this);
  endtask
endclass
```

실행 결과 예상:
```
[TEST] 랜덤 후 커버리지: 72.3%      ← 랜덤만으로는 부족
[TEST] 타겟 후 커버리지: 96.1%      ← 타겟 시퀀스로 목표 달성!
```

### 14.6.2 커버리지 기반 테스트 전략

```systemverilog
// ============================================================
// 커버리지 갭을 채우는 타겟 시퀀스
// ============================================================
class apb_coverage_target_seq extends uvm_sequence#(apb_seq_item);
  `uvm_object_utils(apb_coverage_target_seq)

  function new(string name = "apb_coverage_target_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_seq_item req;

    `uvm_info(get_type_name(), "=== 커버리지 타겟 시퀀스 시작 ===", UVM_LOW)

    // Gap 1: 미접근 주소에 쓰기/읽기
    foreach ({4'hE, 4'hF}[i]) begin
      req = apb_seq_item::type_id::create("req");
      start_item(req);
      if (!req.randomize() with { paddr == (i == 0 ? 4'hE : 4'hF); pwrite == 1; })
        `uvm_error(get_type_name(), "Randomization failed")
      finish_item(req);

      req = apb_seq_item::type_id::create("req");
      start_item(req);
      if (!req.randomize() with { paddr == (i == 0 ? 4'hE : 4'hF); pwrite == 0; })
        `uvm_error(get_type_name(), "Randomization failed")
      finish_item(req);
    end

    // Gap 2: 경계값 데이터 (0xFF)
    req = apb_seq_item::type_id::create("req");
    start_item(req);
    if (!req.randomize() with { paddr == 4'h0; pwrite == 1; pwdata == 8'hFF; })
      `uvm_error(get_type_name(), "Randomization failed")
    finish_item(req);

    // Gap 3: 미실행 조합 (ctrl+read, status+write)
    req = apb_seq_item::type_id::create("req");
    start_item(req);
    if (!req.randomize() with { paddr == 4'h0; pwrite == 0; })  // ctrl+read
      `uvm_error(get_type_name(), "Randomization failed")
    finish_item(req);

    req = apb_seq_item::type_id::create("req");
    start_item(req);
    if (!req.randomize() with { paddr == 4'h1; pwrite == 1; pwdata == 8'hAA; })  // status+write
      `uvm_error(get_type_name(), "Randomization failed")
    finish_item(req);

    `uvm_info(get_type_name(), "=== 커버리지 타겟 시퀀스 완료 ===", UVM_LOW)
  endtask
endclass
```

**커버리지 클로저 프로세스:**

```
커버리지 클로저 프로세스

┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ 1. 랜덤     │     │ 2. 리포트    │     │ 3. 분석     │
│ 테스트 실행  │────▶│ 확인         │────▶│ 미달 항목    │
│ (시퀀스)     │     │ (coverage %) │     │ 파악        │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
┌─────────────┐     ┌──────────────┐     ┌──────▼──────┐
│ 6. 목표     │     │ 5. 재실행    │     │ 4. 타겟     │
│ 달성!       │◀────│ + 머지       │◀────│ 시퀀스 작성  │
│ (≥95%)      │     │ (커버리지)   │     │ (gap 보완)  │
└─────────────┘     └──────────────┘     └─────────────┘
```

### 14.6.3 Ch.11~14 검증 인프라 종합

지금까지 만든 APB 검증 인프라의 전체 그림:

```
Ch.11~14 검증 인프라 종합

┌──────────────────────────────────────────────────────────┐
│  Ch.14 검증 자동화                                       │
│  ┌────────────────────┐  ┌────────────────────────────┐ │
│  │ Coverage Collector  │  │ Assertion Module (SVA)     │ │
│  │ (covergroup)        │  │ R1: Setup→Access          │ │
│  │ addr, write, data   │  │ R2: Transfer Complete     │ │
│  │ cross combinations  │  │ R3~R5: Signal Stability   │ │
│  └─────────┬──────────┘  └────────────────────────────┘ │
├────────────┼────────────────────────────────────────────┤
│  Ch.13 고급 시퀀스                                       │
│  ┌────────────────────┐  ┌────────────────────────────┐ │
│  │ Virtual Sequencer   │  │ Sequence Library           │ │
│  │ Virtual Sequence    │  │ (RAND, RANDC, ITEM, USER) │ │
│  └────────────────────┘  └────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  Ch.12 레지스터 모델 (RAL)                               │
│  ┌────────────────────┐  ┌────────────────────────────┐ │
│  │ Register Model      │  │ Adapter + Predictor       │ │
│  │ (field→reg→block)   │  │ (auto-mirror)             │ │
│  └────────────────────┘  └────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  Ch.11 APB 에이전트                                      │
│  ┌────────────────────┐  ┌────────────────────────────┐ │
│  │ Driver + Monitor    │  │ Scoreboard                │ │
│  │ (BFM pattern)       │  │ (data checking)           │ │
│  └────────────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

| 챕터 | 역할 | 핵심 질문 |
|------|------|-----------|
| **Ch.11** | APB 에이전트 | "신호를 어떻게 주고받는가?" |
| **Ch.12** | RAL | "레지스터를 어떻게 추상화하는가?" |
| **Ch.13** | 가상 시퀀스 | "여러 에이전트를 어떻게 조율하는가?" |
| **Ch.14** | 커버리지+어서션 | "검증이 충분한가? 규칙을 지켰는가?" |

### 14.6.4 실무 커버리지/어서션 가이드

**커버리지 Best Practices:**

| 항목 | 권장 | 이유 |
|------|------|------|
| **목표** | 90~95% | 100%는 비현실적, 나머지는 waiver 문서화 |
| **bins 설계** | 의미 있는 그룹 | auto_bin은 too many bins 유발 |
| **cross** | 2~3차원 | 4차원 이상은 bin 폭발 |
| **per_instance** | 켜기 | 인스턴스별 추적으로 디버깅 용이 |
| **report_phase** | 활용 | 시뮬레이션 종료 시 자동 리포트 |

**어서션 Best Practices:**

| 항목 | 권장 | 이유 |
|------|------|------|
| **disable iff** | 리셋 시 비활성화 | 리셋 중 X 값으로 인한 오탐 방지 |
| **cover property** | 함께 사용 | 어서션이 실제 트리거되었는지 확인 |
| **네이밍** | `assert_규칙명` | 위반 시 어떤 규칙인지 즉시 파악 |
| **$past()** | 안정성 검사에 활용 | 이전 사이클 값과 비교 |
| **bind** | DUT 수정 없이 추가 | 실무에서 RTL 코드 보호 |

**Top 5 커버리지/어서션 실수:**

| 순위 | 실수 | 해결법 |
|------|------|--------|
| 1 | covergroup `new()` 누락 | 생성자에서 반드시 `cg = new()` |
| 2 | `sample()` 호출 누락 | `write()` 안에서 `cg.sample()` |
| 3 | 어서션에 `disable iff` 누락 | 리셋 신호로 비활성화 |
| 4 | cross bin 폭발 (메모리 부족) | `ignore_bins`로 불필요한 조합 제거 |
| 5 | cover property 미사용 | 어서션이 트리거되지 않으면 검증 구멍 |

---

## 14.7 체크포인트

### 14.7.1 셀프 체크

> **Q1**: covergroup, coverpoint, bins의 관계는?
<details>
<summary>정답 보기</summary>
covergroup은 커버리지를 수집하는 컨테이너입니다. coverpoint는 관찰할 변수를 지정합니다. bins는 coverpoint 내에서 값을 의미 있는 그룹으로 분류합니다. `covergroup { coverpoint { bins } }`
</details>

> **Q2**: cross 커버리지가 필요한 이유는?
<details>
<summary>정답 보기</summary>
개별 coverpoint만으로는 **조합**을 추적할 수 없습니다. 예를 들어, 주소 0x0에 읽기가 실행되었는지, 쓰기가 실행되었는지를 구분하려면 addr×write cross가 필요합니다.
</details>

> **Q3**: UVM 커버리지 컬렉터는 어떤 클래스를 상속하는가?
<details>
<summary>정답 보기</summary>
`uvm_subscriber#(트랜잭션_타입)`을 상속합니다. `write()` 메서드를 오버라이드하여 analysis port에서 트랜잭션을 수신하고, covergroup의 `sample()`을 호출합니다.
</details>

> **Q4**: `|->` 와 `|=>`의 차이는?
<details>
<summary>정답 보기</summary>
`|->` (겹침 함축)는 **같은 사이클**에서 결과를 검사합니다. `|=>` (비겹침 함축)는 **다음 사이클**에서 결과를 검사합니다. APB에서 "Setup 다음 사이클에 Access"는 `|=>`를 사용합니다.
</details>

> **Q5**: 어서션에 `disable iff (!resetn)`을 쓰는 이유는?
<details>
<summary>정답 보기</summary>
리셋 중에는 신호가 X 또는 불안정 상태일 수 있어 어서션이 불필요하게 실패합니다. `disable iff`로 리셋 기간 동안 어서션을 비활성화하여 **오탐(false positive)**을 방지합니다.
</details>

> **Q6**: 커버리지 목표를 100%로 설정하지 않는 이유는?
<details>
<summary>정답 보기</summary>
모든 조합이 의미 있는 것은 아닙니다. 예: 읽기 전용 레지스터에 쓰기 조합은 불필요. 실무에서는 **90~95%**를 목표로 하고, 나머지는 `ignore_bins`로 제외하거나 waiver 문서를 작성합니다.
</details>

### 14.7.2 연습문제

**[기본] 연습 1: 커버리지 bins 추가**

`apb_coverage_collector`에 연속 접근 패턴(같은 주소에 2회 연속 접근) 전이 커버리지를 추가하세요.

<details>
<summary>힌트</summary>

```systemverilog
cp_addr_trans: coverpoint addr {
  bins same_addr_repeat = (4'h0[*2]), (4'h1[*2]), (4'h2[*2]);
  // 또는
  bins same_addr = (addr => addr);  // 같은 주소 연속
}
```
</details>

**[중급] 연습 2: 어서션 추가**

APB 프로토콜 어서션 모듈에 다음 규칙을 추가하세요: "psel이 0이면 penable도 반드시 0이어야 한다."

<details>
<summary>힌트</summary>

```systemverilog
property p_no_enable_without_sel;
  @(posedge clk) disable iff (!resetn)
  (!psel) |-> (!penable);
endproperty

assert_no_enable_without_sel: assert property (p_no_enable_without_sel)
else $error("[APB] penable active without psel!");
```
</details>

**[고급] 연습 3: 커버리지 클로저**

현재 커버리지 리포트에서 `cx_addr_dir`의 `general[10]+write` bin이 미달입니다. 이 갭을 채우는 타겟 시퀀스를 작성하세요.

<details>
<summary>힌트</summary>

```systemverilog
class apb_target_addr10_seq extends uvm_sequence#(apb_seq_item);
  virtual task body();
    apb_seq_item req;
    req = apb_seq_item::type_id::create("req");
    start_item(req);
    req.randomize() with { paddr == 4'hA; pwrite == 1; };
    finish_item(req);
  endtask
endclass
```
</details>

### 14.7.3 이 챕터에서 배운 것

이 챕터에서 추가한 검증 자동화 관련 파일:

```
apb_verification/
├── rtl/
│   └── apb_slave_memory.sv        ← Ch.11 (변경 없음)
├── tb/
│   ├── apb_if.sv                  ← Ch.11 (변경 없음)
│   ├── apb_seq_item.sv            ← Ch.11 (변경 없음)
│   ├── apb_driver.sv              ← Ch.11 (변경 없음)
│   ├── apb_monitor.sv             ← Ch.11 (변경 없음)
│   ├── apb_agent.sv               ← Ch.11 (변경 없음)
│   ├── apb_reg_classes.sv         ← Ch.12 (변경 없음)
│   ├── apb_reg_block.sv           ← Ch.12 (변경 없음)
│   ├── apb_reg_adapter.sv         ← Ch.12 (변경 없음)
│   ├── apb_virtual_sequencer.sv   ← Ch.13 (변경 없음)
│   ├── apb_virtual_env.sv         ← Ch.13 (변경 없음)
│   ├── apb_coverage_collector.sv  ← NEW: 커버리지 컬렉터
│   ├── apb_protocol_assertions.sv ← NEW: APB 프로토콜 어서션
│   ├── apb_coverage_env.sv        ← NEW: 커버리지 포함 환경
│   ├── apb_coverage_target_seq.sv ← NEW: 커버리지 타겟 시퀀스
│   └── apb_coverage_test.sv       ← NEW: 커버리지 테스트
└── sim/
    └── run.do
```

Ch.11~13의 코드는 **한 줄도 변경하지 않았습니다.** 커버리지 컬렉터는 기존 모니터의 analysis port에 **추가 구독자**로 연결되고, 어서션 모듈은 DUT 옆에 **독립적으로** 배치됩니다.

### 14.7.4 다음 장 미리보기

Chapter 15에서는 **프로젝트 종합**을 합니다. Ch.1~14에서 배운 모든 기술을 하나의 완성된 프로젝트로 통합합니다. APB Slave Memory에 대한 **완전한 검증 환경**(에이전트 + RAL + 가상 시퀀스 + 커버리지 + 어서션)을 구축하고, 실무 프로젝트 구조로 정리합니다.

**Part 3 진행 현황:**

| 챕터 | 주제 | 핵심 | 상태 |
|------|------|------|------|
| **Ch.11** | 인터페이스와 BFM | APB 에이전트 구축 | ✅ 완료 |
| **Ch.12** | 레지스터 모델 (RAL) | APB 위에 RAL 계층 추가 | ✅ 완료 |
| **Ch.13** | 고급 시퀀스 | 가상 시퀀스, 시퀀스 라이브러리 | ✅ 완료 |
| **Ch.14** | 검증 자동화 | 커버리지, 어서션 | ✅ 지금 여기! |
| **Ch.15** | 프로젝트 종합 | 전체 통합 및 리뷰 | 다음 |

> 💡 **핵심 메시지**: Ch.11에서 "신호를 주고받는 환경"을 만들고, Ch.12에서 "레지스터를 추상화"하고, Ch.13에서 "여러 에이전트를 지휘"하고, Ch.14에서 "검증이 충분한지 측정하고 규칙을 감시"하는 기능을 추가했습니다. 이제 남은 것은 Ch.15에서 **모든 것을 하나로 통합**하는 것입니다.
