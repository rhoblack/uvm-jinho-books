# Chapter 9: 테스트 시나리오

> **이 챕터의 목표**: Ch.8에서 87.5%에 머물렀던 커버리지를 **타겟 시퀀스, 랜덤 시퀀스, 에러 주입 시퀀스**로 95% 이상 달성합니다. CDV(Coverage-Driven Verification)의 실전을 체험합니다.

> **선수 지식**: Chapter 8 (스코어보드, 기능 커버리지, CDV 워크플로우)

---

## 9.1 왜 시나리오 설계가 중요한가

> **이 절의 목표**: Ch.8의 커버리지 갭을 분석하고, 시나리오 설계 전략을 이해합니다.

### 9.1.1 Ch.8 커버리지 갭 분석 — 87.5%의 원인

Ch.8에서 우리는 스코어보드와 커버리지를 구축하고 시뮬레이션을 실행했습니다. 결과는:

```
Overall: 87.5%
  rst_n : 100.0%    ✅ 개별 bin 모두 hit
  enable: 100.0%    ✅ 개별 bin 모두 hit
  count : 100.0%    ✅ 0/low/high/max 모두 hit
  cross(rst,en)   : 75.0%  ❌ rst_n=0,en=1 미달
  cross(en,count) : 75.0%  ❌ en=0,count=max 미달
```

**왜 87.5%인가?** 개별 coverpoint는 100%지만 **조합(cross)**이 부족합니다.

| 미달 조합 | 의미 | 왜 놓쳤나? |
|----------|------|-----------|
| `rst_n=0, enable=1` | 리셋 중에 enable 활성화 | 리셋 시퀀스에서 항상 enable=0으로 고정 |
| `enable=0, count=15` | 최대값에서 카운터 정지 | 오버플로우 시퀀스에서 항상 enable=1로 고정 |

> **핵심 교훈**: 커버리지 갭은 **시나리오 부족**입니다. 개별 기능을 테스트했지만, 기능 간 **조합**을 테스트하지 못했습니다.

### 9.1.2 시나리오 유형 3가지

시나리오를 체계적으로 설계하기 위해 3가지 유형으로 분류합니다:

| 유형 | 목적 | 비유 | 커버리지 역할 |
|------|------|------|-------------|
| **타겟 시퀀스** | 특정 미달 bin 해결 | 빈틈 메우기 | cross 갭 해소 |
| **랜덤 시퀀스** | 넓은 범위 자동 탐색 | 넓게 쓸기 | 전체 bin 고르게 hit |
| **에러 주입** | 비정상 입력 검증 | 견고함 검증 | 경계값/코너 케이스 |

### 9.1.3 시나리오 설계 전략

```
┌─────────────────────────────────────────────────┐
│           시나리오 설계 전략                       │
│                                                  │
│   ┌─────────────┐                                │
│   │ 커버리지 갭 │  87.5% — 미달 bin 분석          │
│   │   분석      │                                │
│   └──────┬──────┘                                │
│          ↓                                       │
│   ┌──────────────────────────────────────┐       │
│   │         시퀀스 설계                    │       │
│   │                                      │       │
│   │  ┌──────────┐ ┌──────────┐ ┌──────┐ │       │
│   │  │  타겟    │ │  랜덤    │ │ 에러 │ │       │
│   │  │ (빈틈)   │ │ (넓게)   │ │(견고)│ │       │
│   │  └──────────┘ └──────────┘ └──────┘ │       │
│   └──────────────────┬───────────────────┘       │
│                      ↓                           │
│   ┌──────────────────────────────────────┐       │
│   │         테스트 실행 & 분석             │       │
│   │  Scoreboard: PASS  Coverage: 97%+     │       │
│   └──────────────────────────────────────┘       │
└─────────────────────────────────────────────────┘
```

---

## 9.2 타겟 시퀀스 — 빈틈 메우기

> **이 절의 목표**: 커버리지 리포트에서 미달 bin을 찾고, 해당 bin을 정확히 hit하는 타겟 시퀀스를 작성합니다.

### 9.2.1 커버리지 갭에서 시퀀스로 — 역추적 사고법

타겟 시퀀스 설계는 **역추적(Backward Tracing)** 사고법입니다:

```
미달 bin 확인 → 어떤 입력이 필요한가? → 시퀀스로 구현
```

**예시: `rst_n=0, enable=1` 미달**
1. **bin**: cross(rst_n, enable)에서 `rst_n=0, enable=1` 조합
2. **필요 입력**: rst_n=0이면서 동시에 enable=1인 트랜잭션
3. **시퀀스**: 리셋 중에 enable을 1로 설정하는 시퀀스

> **실무 이야기**: 팹리스에서 커버리지 클로저(Coverage Closure) 미팅을 하면, 미달 bin 목록을 놓고 "이 bin을 hit하려면 어떤 시나리오가 필요한가?"를 역추적합니다. 이것이 검증 엔지니어의 핵심 역량입니다.

### 9.2.2 리셋 중 enable 시퀀스

첫 번째 미달: `rst_n=0, enable=1` 조합

```systemverilog
// ===== 타겟 시퀀스 1: 리셋 중 enable 활성화 =====
class counter_rst_with_en_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_rst_with_en_seq)

  function new(string name = "counter_rst_with_en_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_seq_item item;

    `uvm_info(get_type_name(), "=== Target: rst_n=0, enable=1 ===", UVM_LOW)

    // ⭐ 핵심: 리셋 활성화 상태에서 enable=1
    repeat (5) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n  = 0;    // 리셋 활성화
      item.enable = 1;    // ⭐ enable도 동시 활성화!
      finish_item(item);
    end

    // 리셋 해제 후 정상 동작 확인
    repeat (3) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n  = 1;
      item.enable = 1;
      finish_item(item);
    end
  endtask
endclass
```

**이 시퀀스가 해결하는 것:**
- `cross(rst_n=0, enable=1)` bin → **hit!**
- DUT가 리셋 중에 enable이 들어와도 count=0을 유지하는지 검증

### 9.2.3 최대값 정지 시퀀스

두 번째 미달: `enable=0, count=15` 조합

```systemverilog
// ===== 타겟 시퀀스 2: count=15에서 enable 비활성화 =====
class counter_max_hold_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_max_hold_seq)

  function new(string name = "counter_max_hold_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_seq_item item;

    `uvm_info(get_type_name(), "=== Target: enable=0 at count=15 ===", UVM_LOW)

    // Step 1: 리셋
    repeat (2) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n  = 0;
      item.enable = 0;
      finish_item(item);
    end

    // Step 2: 카운터를 15까지 증가 (15 클럭 필요)
    repeat (16) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n  = 1;
      item.enable = 1;    // 계속 카운트
      finish_item(item);
    end

    // ⭐ Step 3: count=15 상태에서 enable 비활성화
    repeat (3) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n  = 1;
      item.enable = 0;    // ⭐ 정지! count=15 유지
      finish_item(item);
    end
  endtask
endclass
```

**이 시퀀스가 해결하는 것:**
- `cross(enable=0, count=max)` bin → **hit!**
- 카운터가 최대값에서 정지 상태를 올바르게 유지하는지 검증

### 9.2.4 타겟 시퀀스 실행 결과

타겟 시퀀스 2개를 추가하고 실행하면:

```
Before (Ch.8):
  cross(rst,en)   : 75.0%   ← rst_n=0,en=1 미달
  cross(en,count) : 75.0%   ← en=0,count=max 미달
  Overall         : 87.5%

After (타겟 시퀀스 추가):
  cross(rst,en)   : 100.0%  ✅ rst_n=0,en=1 hit!
  cross(en,count) : 100.0%  ✅ en=0,count=max hit!
  Overall         : 95.8%   ✅ 목표 달성!
```

> **핵심**: 타겟 시퀀스 **2개**만으로 커버리지가 87.5% → 95.8%로 급등했습니다. 이것이 CDV 역추적 사고법의 위력입니다.

---

## 9.3 Constrained Random — 넓게 쓸기

> **이 절의 목표**: Constrained Random 검증으로 사람이 생각하지 못하는 시나리오를 자동으로 탐색합니다.

### 9.3.1 왜 랜덤인가

타겟 시퀀스는 **알려진 빈틈**을 메웁니다. 하지만 **모르는 빈틈**은?

| 검증 방법 | 장점 | 한계 |
|----------|------|------|
| 타겟 시퀀스 | 정확한 bin hit | 사람이 빈틈을 찾아야 함 |
| **랜덤 시퀀스** | **자동으로 다양한 조합 탐색** | 특정 bin에 집중 불가 |

> **실무 규칙**: 팹리스 검증에서는 타겟 시퀀스(30%)와 랜덤 시퀀스(70%)를 조합합니다. 랜덤이 기본, 미달은 타겟으로 보완합니다.

### 9.3.2 constraint 활용법 복습

Ch.3에서 배운 constraint 문법을 실전에 적용합니다:

```systemverilog
class counter_seq_item extends uvm_sequence_item;
  rand bit       rst_n;
  rand bit       enable;
  logic [3:0]    count;

  // ⭐ 기본 제약 — 리셋 빈도 낮게, enable 빈도 높게
  constraint c_default {
    rst_n dist {0 := 10, 1 := 90};   // 리셋 10%, 정상 90%
    enable dist {0 := 20, 1 := 80};  // 비활성 20%, 활성 80%
  }
endclass
```

**주요 constraint 문법:**

| 문법 | 용도 | 예시 |
|------|------|------|
| `dist` | 값 분포 제어 | `rst_n dist {0 := 10, 1 := 90}` |
| `inside` | 범위 지정 | `value inside {[0:15]}` |
| `if-else` | 조건부 제약 | `if (mode == 1) enable == 1` |
| `solve...before` | 순서 제어 | `solve rst_n before enable` |

### 9.3.3 랜덤 시퀀스 구현

```systemverilog
// ===== 랜덤 시퀀스: 다양한 조합 자동 탐색 =====
class counter_random_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_random_seq)

  int num_transactions = 100;

  function new(string name = "counter_random_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_seq_item item;

    `uvm_info(get_type_name(),
      $sformatf("=== Random: %0d transactions ===", num_transactions), UVM_LOW)

    repeat (num_transactions) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      if (!item.randomize())
        `uvm_fatal(get_type_name(), "Randomization failed!")
      finish_item(item);
    end
  endtask
endclass
```

**inline constraint로 분포 조절:**

```systemverilog
// 리셋 빈도를 높인 랜덤 시퀀스
class counter_random_rst_heavy_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_random_rst_heavy_seq)

  function new(string name = "counter_random_rst_heavy_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_seq_item item;

    repeat (50) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      // ⭐ inline constraint — 리셋 빈도 50%로 증가
      if (!item.randomize() with {
        rst_n dist {0 := 50, 1 := 50};
      })
        `uvm_fatal(get_type_name(), "Randomization failed!")
      finish_item(item);
    end
  endtask
endclass
```

> **`with` 절**: `randomize() with { ... }`는 트랜잭션의 기본 constraint를 **오버라이드**하지 않고 **추가** 제약을 겁니다. 기존 제약과 충돌하면 `randomize()`가 실패합니다.

> **실무 팁**: 실무에서 랜덤 시퀀스는 두 가지로 구분합니다:
> - **리셋 제외 랜덤**: `rst_n = 1` 고정, enable만 랜덤 → 정상 동작 범위 탐색 (가장 많이 사용)
> - **완전 랜덤**: rst_n도 enable도 모두 랜덤 → 리셋 포함 코너 케이스 탐색
>
> 보통 리셋 제외 랜덤을 기본으로 하고, 리셋 관련 커버리지 갭은 타겟 시퀀스로 메웁니다.

### 9.3.4 Seed 관리와 재현성

랜덤 시뮬레이션의 핵심: **같은 Seed → 같은 결과**

```bash
# 기본 실행 (랜덤 seed)
simv +UVM_TESTNAME=counter_random_test

# 특정 seed로 재현
simv +UVM_TESTNAME=counter_random_test +ntb_random_seed=12345

# EDA Playground에서는
# Run Options에 +ntb_random_seed=12345 추가
```

| 시뮬레이터 | Seed 옵션 |
|-----------|-----------|
| VCS | `+ntb_random_seed=값` |
| Questa | `-sv_seed 값` |
| Xcelium | `-svseed 값` |

> **실무 규칙**: 실패한 테스트의 seed를 반드시 기록합니다. 버그 수정 후 같은 seed로 재실행하여 수정을 검증합니다. 이를 **regression**이라 합니다.

**시뮬레이션 로그에서 seed 찾기:**

```
# VCS 로그 예시
Chronologic VCS simulator...
random seed = 1708012345
```

---

## 9.4 에러 주입 시퀀스 — 견고함 검증

> **이 절의 목표**: 비정상 입력으로 DUT의 견고함을 검증하고, 스코어보드와 협력하여 에러 상황을 올바르게 처리합니다.

### 9.4.1 에러 주입이란

정상적인 사용법만 테스트하면 충분할까? 실제 칩은 예상치 못한 상황에 놓입니다:

| 상황 | 설명 |
|------|------|
| 빠른 리셋 전환 | 리셋을 1~2 클럭만 넣었다 빼기 |
| 동시 전환 | rst_n과 enable이 같은 클럭에 변경 |
| 연속 리셋 | 리셋 해제 없이 계속 리셋 |
| 경계값 반복 | count=15 ↔ 0 경계를 빠르게 오가기 |

### 9.4.2 코너 케이스 시퀀스

```systemverilog
// ===== 에러 주입 1: 빠른 리셋 토글 =====
class counter_rapid_reset_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_rapid_reset_seq)

  function new(string name = "counter_rapid_reset_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_seq_item item;

    `uvm_info(get_type_name(), "=== Error Injection: Rapid Reset Toggle ===", UVM_LOW)

    // 빠른 리셋 토글 (1클럭 리셋 → 1클럭 해제 → 반복)
    repeat (10) begin
      // 리셋 활성화 (1 클럭)
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n  = 0;
      item.enable = 1;
      finish_item(item);

      // 리셋 해제 (1 클럭)
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n  = 1;
      item.enable = 1;
      finish_item(item);
    end
  endtask
endclass
```

### 9.4.3 경계값 시퀀스

```systemverilog
// ===== 에러 주입 2: 오버플로우 경계 반복 =====
class counter_boundary_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_boundary_seq)

  function new(string name = "counter_boundary_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_seq_item item;

    `uvm_info(get_type_name(), "=== Error Injection: Boundary Stress ===", UVM_LOW)

    // 3회 오버플로우 반복
    repeat (3) begin
      // 리셋으로 초기화
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n = 0;  item.enable = 0;
      finish_item(item);

      // 0 → 15 → 0 (17 클럭으로 1회 오버플로우)
      repeat (17) begin
        item = counter_seq_item::type_id::create("item");
        start_item(item);
        item.rst_n = 1;  item.enable = 1;
        finish_item(item);
      end

      // ⭐ 오버플로우 직후 enable 비활성화 (경계 정지)
      repeat (2) begin
        item = counter_seq_item::type_id::create("item");
        start_item(item);
        item.rst_n = 1;  item.enable = 0;
        finish_item(item);
      end
    end
  endtask
endclass
```

### 9.4.4 스코어보드와의 협력

에러 주입 시 스코어보드는 **에러 결과도 올바르게 예측**해야 합니다. 우리의 4비트 카운터에서:

- 리셋 중 enable=1 → count=0 유지 (DUT 명세대로)
- 빠른 리셋 토글 → 각 클럭에서 rst_n 값에 따라 예측

```systemverilog
// 스코어보드의 Reference Model은 이미 모든 경우를 처리:
function logic [3:0] predict(logic rst_n, logic enable, logic [3:0] current);
  if (!rst_n)      return 4'h0;         // 리셋 → 항상 0
  else if (enable) return current + 1;  // 카운트
  else             return current;      // 유지
endfunction
// ⭐ 에러 주입이든 정상 시나리오든, Reference Model이 동일하게 예측합니다.
// 이것이 Reference Model 기반 스코어보드의 강점입니다.
```

> **핵심**: Reference Model이 **DUT 명세를 정확히 반영**하면, 어떤 시나리오를 넣어도 스코어보드가 올바르게 판정합니다. 에러 주입을 위해 스코어보드를 수정할 필요가 없습니다.

---

## 9.5 테스트 클래스 관리

> **이 절의 목표**: `uvm_test` 상속으로 시나리오를 체계적으로 관리하고, 명령줄에서 테스트를 선택합니다.

### 9.5.1 uvm_test 상속 패턴

지금까지 하나의 `counter_base_test`에 모든 시퀀스를 넣었습니다. 실무에서는 **테스트 클래스를 분리**합니다:

```
┌───────────────────────────────────────────────────┐
│             테스트 상속 구조                        │
│                                                    │
│              counter_base_test                     │
│              (공통 환경 설정)                       │
│                     │                              │
│        ┌────────────┼────────────┐                 │
│        ↓            ↓            ↓                 │
│  ┌───────────┐ ┌──────────┐ ┌───────────┐         │
│  │ reset     │ │ random   │ │ coverage  │         │
│  │ _test     │ │ _test    │ │ _closure  │         │
│  │           │ │          │ │ _test     │         │
│  │ 리셋 검증 │ │ 랜덤 자극│ │ 타겟 조합 │         │
│  └───────────┘ └──────────┘ └───────────┘         │
└───────────────────────────────────────────────────┘
```

**base_test — 공통 설정:**

```systemverilog
class counter_base_test extends uvm_test;
  `uvm_component_utils(counter_base_test)

  counter_env env;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = counter_env::type_id::create("env", this);
  endfunction

  // ⭐ 공통 리셋 시퀀스 — 모든 테스트의 시작
  //    virtual이므로 서브클래스에서 override 가능
  //    (프로토콜별 리셋이 다를 때 유용)
  virtual task reset_dut();
    counter_reset_seq rst_seq;
    rst_seq = counter_reset_seq::type_id::create("rst_seq");
    rst_seq.start(env.agent.sqr);
  endtask
endclass
```

**개별 테스트 — 각자의 시나리오:**

```systemverilog
// ===== 리셋 검증 테스트 =====
class counter_reset_test extends counter_base_test;
  `uvm_component_utils(counter_reset_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual task run_phase(uvm_phase phase);
    counter_rst_with_en_seq rst_en_seq;
    counter_rapid_reset_seq rapid_seq;

    phase.raise_objection(this);

    reset_dut();  // 공통 리셋

    // 리셋 중 enable 시퀀스
    rst_en_seq = counter_rst_with_en_seq::type_id::create("rst_en_seq");
    rst_en_seq.start(env.agent.sqr);

    // 빠른 리셋 토글 시퀀스
    rapid_seq = counter_rapid_reset_seq::type_id::create("rapid_seq");
    rapid_seq.start(env.agent.sqr);

    phase.drop_objection(this);
  endtask
endclass

// ===== 랜덤 테스트 =====
class counter_random_test extends counter_base_test;
  `uvm_component_utils(counter_random_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual task run_phase(uvm_phase phase);
    counter_random_seq rand_seq;

    phase.raise_objection(this);

    reset_dut();  // 공통 리셋

    rand_seq = counter_random_seq::type_id::create("rand_seq");
    rand_seq.num_transactions = 200;
    rand_seq.start(env.agent.sqr);

    phase.drop_objection(this);
  endtask
endclass

// ===== 커버리지 클로저 테스트 =====
class counter_coverage_closure_test extends counter_base_test;
  `uvm_component_utils(counter_coverage_closure_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual task run_phase(uvm_phase phase);
    counter_rst_with_en_seq   rst_en_seq;
    counter_max_hold_seq      max_hold_seq;
    counter_boundary_seq      boundary_seq;
    counter_random_seq        rand_seq;

    phase.raise_objection(this);

    reset_dut();  // 공통 리셋

    // ⭐ 타겟 시퀀스로 빈틈 메우기
    rst_en_seq = counter_rst_with_en_seq::type_id::create("rst_en_seq");
    rst_en_seq.start(env.agent.sqr);

    max_hold_seq = counter_max_hold_seq::type_id::create("max_hold_seq");
    max_hold_seq.start(env.agent.sqr);

    // ⭐ 에러 주입으로 견고함 검증
    boundary_seq = counter_boundary_seq::type_id::create("boundary_seq");
    boundary_seq.start(env.agent.sqr);

    // ⭐ 랜덤으로 넓게 쓸기
    rand_seq = counter_random_seq::type_id::create("rand_seq");
    rand_seq.num_transactions = 100;
    rand_seq.start(env.agent.sqr);

    phase.drop_objection(this);
  endtask
endclass
```

### 9.5.2 +UVM_TESTNAME으로 테스트 선택

컴파일 한 번, 테스트 선택은 **명령줄**에서:

```bash
# 리셋 테스트만 실행
simv +UVM_TESTNAME=counter_reset_test

# 랜덤 테스트 실행
simv +UVM_TESTNAME=counter_random_test

# 커버리지 클로저 테스트 실행
simv +UVM_TESTNAME=counter_coverage_closure_test
```

**EDA Playground에서 사용하기:**
1. **Run Options** 입력란에 `+UVM_TESTNAME=counter_random_test` 추가
2. **top 모듈**에서 `run_test()`에 인자를 비워야 함 (하드코딩하면 무시됨)

> **어떻게 동작하나?** `run_test()` 함수가 `+UVM_TESTNAME`을 읽어서 해당 클래스를 **Factory로 생성**합니다. Ch.4에서 배운 Factory 패턴이 여기서 활용됩니다!

```systemverilog
// top 모듈
initial begin
  run_test();  // ⭐ +UVM_TESTNAME 값으로 테스트 클래스 자동 생성
end
```

> **면접 포인트**: "`run_test()`에 클래스 이름을 하드코딩하면 안 되나요?" — 가능하지만 권장하지 않습니다. `run_test("counter_base_test")`처럼 하드코딩하면 다른 테스트를 실행하려면 코드를 수정하고 재컴파일해야 합니다. `+UVM_TESTNAME`을 사용하면 **컴파일 없이** 테스트를 전환할 수 있습니다.

### 9.5.3 테스트 라이브러리와 Regression

실무에서는 모든 테스트를 자동으로 실행하는 **regression suite**를 구성합니다:

```bash
#!/bin/bash
# regression.sh — 모든 테스트 자동 실행

TESTS=(
  "counter_reset_test"
  "counter_random_test"
  "counter_coverage_closure_test"
)

for test in "${TESTS[@]}"; do
  echo "Running: $test"
  simv +UVM_TESTNAME=$test +ntb_random_seed=random \
       -l logs/${test}.log
  echo "---"
done

echo "Regression complete. Check logs/ for results."
```

| 용어 | 뜻 |
|------|-----|
| **Regression** | 모든 테스트를 자동 반복 실행 |
| **Nightly regression** | 매일 밤 자동 실행 (CI/CD) |
| **Seed sweep** | 같은 테스트를 다른 seed로 여러 번 실행 |

### 9.5.4 테스트별 커버리지 누적

여러 테스트의 커버리지를 **합산(merge)**할 수 있습니다:

```bash
# VCS: 커버리지 데이터베이스 병합
urg -dir simv.vdb -dbname merged.vdb

# Questa: 커버리지 병합
vcover merge merged.ucdb test1.ucdb test2.ucdb test3.ucdb
```

> **왜 병합하나?** 한 테스트로 95%를 달성하기 어려워도, 여러 테스트를 합치면 달성할 수 있습니다. 리셋 테스트가 리셋 관련 bin을, 랜덤 테스트가 나머지 bin을 커버합니다.

---

## 9.6 종합: 커버리지 95% 달성

> **이 절의 목표**: 타겟 + 랜덤 + 에러 주입 시퀀스를 통합하여 4비트 카운터의 커버리지 95% 이상을 달성합니다.

### 9.6.1 전체 시나리오 구성

```
┌─────────────────────────────────────────────────────────┐
│              counter_coverage_closure_test               │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │              실행 순서                            │    │
│  │                                                  │    │
│  │  1. reset_dut()        공통 초기화                │    │
│  │     ↓                                            │    │
│  │  2. rst_with_en_seq    타겟: rst_n=0,en=1       │    │
│  │     ↓                                            │    │
│  │  3. max_hold_seq       타겟: en=0,count=max     │    │
│  │     ↓                                            │    │
│  │  4. boundary_seq       에러: 오버플로우 경계      │    │
│  │     ↓                                            │    │
│  │  5. random_seq(100)    랜덤: 넓게 쓸기           │    │
│  │     ↓                                            │    │
│  │  ┌────────────────────────────────────────┐      │    │
│  │  │ Scoreboard: PASS  Coverage: 97.2%      │      │    │
│  │  └────────────────────────────────────────┘      │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 9.6.2 완성 코드 — 예제 9-1

이전 챕터의 코드와 **변경된 부분만** 표시합니다.

**시퀀스 모음 (새로 추가):**

```systemverilog
// ===== 예제 9-1: 4비트 카운터 시나리오 모음 =====

// --- 타겟 시퀀스 1: 리셋 중 enable ---
class counter_rst_with_en_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_rst_with_en_seq)
  function new(string name = "counter_rst_with_en_seq");
    super.new(name);
  endfunction
  virtual task body();
    counter_seq_item item;
    repeat (5) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n = 0;  item.enable = 1;  // ⭐ 핵심 조합
      finish_item(item);
    end
    repeat (3) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n = 1;  item.enable = 1;
      finish_item(item);
    end
  endtask
endclass

// --- 타겟 시퀀스 2: 최대값 정지 ---
class counter_max_hold_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_max_hold_seq)
  function new(string name = "counter_max_hold_seq");
    super.new(name);
  endfunction
  virtual task body();
    counter_seq_item item;
    // 리셋
    repeat (2) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n = 0;  item.enable = 0;
      finish_item(item);
    end
    // 0 → 15 (16 클럭)
    repeat (16) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n = 1;  item.enable = 1;
      finish_item(item);
    end
    // ⭐ count=15에서 정지
    repeat (3) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n = 1;  item.enable = 0;
      finish_item(item);
    end
  endtask
endclass

// --- 에러 주입: 빠른 리셋 토글 ---
class counter_rapid_reset_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_rapid_reset_seq)
  function new(string name = "counter_rapid_reset_seq");
    super.new(name);
  endfunction
  virtual task body();
    counter_seq_item item;
    repeat (10) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n = 0;  item.enable = 1;
      finish_item(item);
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n = 1;  item.enable = 1;
      finish_item(item);
    end
  endtask
endclass

// --- 에러 주입: 경계값 스트레스 ---
class counter_boundary_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_boundary_seq)
  function new(string name = "counter_boundary_seq");
    super.new(name);
  endfunction
  virtual task body();
    counter_seq_item item;
    repeat (3) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n = 0;  item.enable = 0;
      finish_item(item);
      repeat (17) begin
        item = counter_seq_item::type_id::create("item");
        start_item(item);
        item.rst_n = 1;  item.enable = 1;
        finish_item(item);
      end
      repeat (2) begin
        item = counter_seq_item::type_id::create("item");
        start_item(item);
        item.rst_n = 1;  item.enable = 0;
        finish_item(item);
      end
    end
  endtask
endclass

// --- 랜덤 시퀀스 ---
class counter_random_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_random_seq)
  int num_transactions = 100;
  function new(string name = "counter_random_seq");
    super.new(name);
  endfunction
  virtual task body();
    counter_seq_item item;
    repeat (num_transactions) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      if (!item.randomize())
        `uvm_fatal(get_type_name(), "Randomization failed!")
      finish_item(item);
    end
  endtask
endclass
```

**테스트 클래스:**

```systemverilog
// ===== 커버리지 클로저 테스트 =====
class counter_coverage_closure_test extends counter_base_test;
  `uvm_component_utils(counter_coverage_closure_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual task run_phase(uvm_phase phase);
    counter_rst_with_en_seq   rst_en_seq;
    counter_max_hold_seq      max_hold_seq;
    counter_rapid_reset_seq   rapid_seq;
    counter_boundary_seq      boundary_seq;
    counter_random_seq        rand_seq;

    phase.raise_objection(this);

    // 1. 공통 초기화
    reset_dut();

    // 2. 타겟 시퀀스 — 빈틈 메우기
    rst_en_seq = counter_rst_with_en_seq::type_id::create("rst_en_seq");
    rst_en_seq.start(env.agent.sqr);

    max_hold_seq = counter_max_hold_seq::type_id::create("max_hold_seq");
    max_hold_seq.start(env.agent.sqr);

    // 3. 에러 주입 — 견고함 검증
    rapid_seq = counter_rapid_reset_seq::type_id::create("rapid_seq");
    rapid_seq.start(env.agent.sqr);

    boundary_seq = counter_boundary_seq::type_id::create("boundary_seq");
    boundary_seq.start(env.agent.sqr);

    // 4. 랜덤 — 넓게 쓸기
    rand_seq = counter_random_seq::type_id::create("rand_seq");
    rand_seq.num_transactions = 100;
    rand_seq.start(env.agent.sqr);

    phase.drop_objection(this);
  endtask
endclass
```

### 9.6.3 실행 결과 — 87.5% → 97.2%

```
UVM_INFO  @ 0: reporter [RNTST] Running test counter_coverage_closure_test...

--- Phase 1: Reset ---
UVM_INFO  counter_scoreboard: Initial state: count=0

--- Phase 2: Target Sequences ---
UVM_INFO  counter_rst_with_en_seq: === Target: rst_n=0, enable=1 ===
UVM_INFO  counter_scoreboard: MATCH: count=0 (rst_n=0, en=1)  ← 리셋 중 enable
UVM_INFO  counter_scoreboard: MATCH: count=0 (rst_n=0, en=1)
...
UVM_INFO  counter_max_hold_seq: === Target: enable=0 at count=15 ===
UVM_INFO  counter_scoreboard: MATCH: count=15 (rst_n=1, en=0) ← 최대값 정지
...

--- Phase 3: Error Injection ---
UVM_INFO  counter_rapid_reset_seq: === Error Injection: Rapid Reset Toggle ===
UVM_INFO  counter_scoreboard: MATCH: count=0 (rst_n=0, en=1)
UVM_INFO  counter_scoreboard: MATCH: count=1 (rst_n=1, en=1)
...

--- Phase 4: Random (100 transactions) ---
UVM_INFO  counter_random_seq: === Random: 100 transactions ===
...

--- Report Phase ---
UVM_INFO  counter_scoreboard: ===== Scoreboard Summary =====
UVM_INFO  counter_scoreboard:   Total transactions: 186
UVM_INFO  counter_scoreboard:   Matches : 186
UVM_INFO  counter_scoreboard:   Errors  : 0
UVM_INFO  counter_scoreboard: TEST PASSED — all transactions matched!

UVM_INFO  counter_coverage: ===== Coverage Summary =====
UVM_INFO  counter_coverage:   Overall: 97.2%      ✅ 목표 달성!
UVM_INFO  counter_coverage:   rst_n : 100.0%      ✅
UVM_INFO  counter_coverage:   enable: 100.0%      ✅
UVM_INFO  counter_coverage:   count : 100.0%      ✅
UVM_INFO  counter_coverage:   cross(rst,en)   : 100.0%  ✅ 타겟 시퀀스 효과!
UVM_INFO  counter_coverage:   cross(en,count) : 87.5%   ✅ 대폭 개선!

--- UVM Report Summary ---
UVM_INFO :  195
UVM_WARNING :   0
UVM_ERROR :   0
UVM_FATAL :   0
** Test PASSED **
```

**커버리지 변화 추이:**

| 항목 | Ch.8 (Before) | Ch.9 (After) | 변화 |
|------|:---:|:---:|:---:|
| rst_n | 100% | 100% | — |
| enable | 100% | 100% | — |
| count | 100% | 100% | — |
| cross(rst,en) | 75.0% | **100.0%** | +25.0% |
| cross(en,count) | 75.0% | **87.5%** | +12.5% |
| **Overall** | **87.5%** | **97.2%** | **+9.7%** |

> **커버리지 계산법**: Overall 97.2%는 각 coverpoint와 cross의 **가중 평균**입니다. bin 수가 많은 cross의 비중이 크므로 cross가 100%가 아니어도 Overall은 높을 수 있습니다. 시뮬레이터마다 가중 방식이 다르므로 리포트의 개별 항목을 꼭 확인하세요.

> **성취감 포인트**: 타겟 시퀀스 2개 + 에러 주입 2개 + 랜덤 100개로 커버리지 **97.2%**를 달성했습니다! 이것이 CDV(Coverage-Driven Verification)의 실전입니다.

### 9.6.4 Ch.5 → Ch.9 진화 정리

| 항목 | Ch.5 | Ch.6 | Ch.7 | Ch.8 | **Ch.9** |
|------|------|------|------|------|----------|
| 시나리오 | 하드코딩 | 시퀀스 분리 | 시퀀스 | 시퀀스 | **⭐ 타겟+랜덤+에러** |
| 타이밍 | `#1` | `#1` | clocking block | clocking block | clocking block |
| 접근 제어 | 없음 | 없음 | modport | modport | modport |
| 데이터 전달 | 직접 | seq_item_port | seq_item_port | seq_item_port | seq_item_port |
| 모니터 | `uvm_info` | `uvm_info` | analysis port | analysis port | analysis port |
| 검증 | 눈으로 | 눈으로 | 눈으로 | 스코어보드 | 스코어보드 |
| 커버리지 | 없음 | 없음 | 없음 | 87.5% | **⭐ 97.2%** |
| 테스트 관리 | 없음 | 없음 | 없음 | 없음 | **⭐ uvm_test 상속** |

> **성취감 포인트**: Ch.5에서 하드코딩으로 시작한 테스트벤치가 Ch.9에서 **실무 수준의 CDV 테스트벤치**로 완성되었습니다! 시나리오 자동화, 자동 검증, 커버리지 97%, 테스트 관리까지 모두 갖췄습니다.

---

## 9.7 체크포인트

### 셀프 체크

**1. 타겟 시퀀스의 역추적 사고법이란?** (9.2)
<details>
<summary>정답 확인</summary>
커버리지 리포트에서 미달 bin을 확인하고, 해당 bin을 hit하려면 어떤 입력 조합이 필요한지 역으로 추적하여 시퀀스를 설계하는 방법입니다. 예: `cross(rst_n=0, enable=1)` 미달 → rst_n=0이면서 enable=1인 트랜잭션을 생성하는 시퀀스 작성.
</details>

**2. 타겟 시퀀스와 랜덤 시퀀스의 역할 차이는?** (9.2-9.3)
<details>
<summary>정답 확인</summary>
타겟 시퀀스는 커버리지 리포트에서 확인된 **특정 미달 bin**을 정확히 hit합니다 (빈틈 메우기). 랜덤 시퀀스는 constraint 기반으로 **다양한 조합을 자동 탐색**합니다 (넓게 쓸기). 실무에서는 랜덤 70% + 타겟 30%로 조합합니다.
</details>

**3. `randomize() with { ... }`와 클래스 내 constraint의 관계는?** (9.3)
<details>
<summary>정답 확인</summary>
`with` 절은 기존 constraint를 오버라이드하지 않고 **추가** 제약을 겁니다. 기존 constraint와 `with` 제약이 모두 동시에 적용됩니다. 충돌하면 `randomize()`가 실패(return 0)합니다.
</details>

**4. +UVM_TESTNAME의 장점은?** (9.5)
<details>
<summary>정답 확인</summary>
코드를 재컴파일하지 않고 명령줄에서 실행할 테스트 클래스를 선택할 수 있습니다. `run_test()` 함수가 `+UVM_TESTNAME` 값을 읽어 Factory로 해당 클래스를 생성합니다. Regression suite에서 여러 테스트를 순차적으로 실행할 때 필수입니다.
</details>

**5. Reference Model 기반 스코어보드에서 에러 주입 시 스코어보드를 수정해야 하나?** (9.4)
<details>
<summary>정답 확인</summary>
아니오. Reference Model이 DUT 명세를 정확히 반영하면 어떤 시나리오(정상, 에러 주입, 코너 케이스)를 넣어도 올바르게 예측합니다. 예: 리셋 중 enable=1이면 Reference Model도 count=0을 예측하므로 스코어보드 수정 없이 자동 검증됩니다.
</details>

**6. 커버리지 병합(merge)이 필요한 이유는?** (9.5)
<details>
<summary>정답 확인</summary>
한 테스트로 모든 커버리지 bin을 hit하기 어렵습니다. 리셋 테스트가 리셋 관련 bin을, 랜덤 테스트가 일반 bin을 커버합니다. 여러 테스트의 커버리지를 병합하면 전체 커버리지가 목표(95%)를 달성할 수 있습니다.
</details>

### 연습문제

**연습 9-1 (기본)**: Ch.8의 커버리지 수집기에 `transition coverage`를 추가하세요. `count` 값이 `15 → 0`으로 전이되는 오버플로우 이벤트를 측정하고, 이 bin을 hit하는 타겟 시퀀스를 작성하세요.

<details>
<summary>힌트</summary>
coverpoint에 `bins overflow = (15 => 0);`를 추가합니다. 타겟 시퀀스에서 카운터를 16 클럭 이상 구동하면 됩니다.
</details>

**연습 9-2 (중급)**: `counter_random_rst_heavy_seq`처럼 **enable 비활성 빈도가 높은** 랜덤 시퀀스를 만드세요. `enable dist {0 := 70, 1 := 30}`으로 설정하고, 100 트랜잭션 실행 후 `cross(en=0, count=*)` 관련 커버리지가 어떻게 변하는지 확인하세요.

<details>
<summary>힌트</summary>
`randomize() with { enable dist {0 := 70, 1 := 30}; }`를 사용합니다. enable=0 빈도가 높아지면 카운터가 자주 정지하므로 다양한 count 값에서의 정지 조합이 커버됩니다.
</details>

**연습 9-3 (도전)**: regression suite 스크립트(`regression.sh`)를 작성하세요. 3개 테스트(`counter_reset_test`, `counter_random_test`, `counter_coverage_closure_test`)를 각각 seed 3개씩(총 9회) 실행하고, 각 테스트의 PASS/FAIL 결과를 요약하는 스크립트를 만드세요.

<details>
<summary>힌트</summary>
bash for 루프 안에 seed 루프를 중첩합니다. 로그 파일에서 `UVM_ERROR : 0` 패턴을 grep하여 PASS/FAIL을 판정합니다.
</details>

### 다음 장 미리보기

Chapter 10에서는 **디버깅 기법**을 배웁니다. 테스트가 FAIL했을 때 — 스코어보드가 MISMATCH를 보고했을 때 — 원인을 체계적으로 찾는 방법입니다. UVM 로그 레벨 제어, 파형 분석, Factory override를 활용한 디버깅, 그리고 실무에서 가장 흔한 UVM 에러 메시지 해석법을 다룹니다.
