# Chapter 6: 시퀀스 & 시퀀서

> **학습 목표**
> - `uvm_sequence_item`으로 트랜잭션을 정의할 수 있다
> - `uvm_sequence`의 `body()`에서 트랜잭션을 생성·전송할 수 있다
> - Sequence-Sequencer-Driver 연결 구조를 이해한다
> - `start_item()`/`finish_item()` 패턴을 사용할 수 있다
> - 여러 시퀀스를 만들어 다양한 테스트 시나리오를 구성할 수 있다

> **선수 지식**: Chapter 3에서 배운 class, randomize, constraint를 사용합니다. Chapter 4의 uvm_object, Factory, Phase, Chapter 5의 테스트벤치 구조(driver, monitor, agent)가 핵심 기반입니다.

---

## 6.1 왜 시퀀스가 필요한가

> **이 절의 목표**: Chapter 5 방식의 한계를 이해하고, 시퀀스를 통한 해결 방향을 파악합니다.

### 6.1.1 Chapter 5 방식의 한계

Chapter 5에서 만든 드라이버를 다시 봅시다:

```systemverilog
// Chapter 5 방식: 드라이버 안에 테스트 시나리오가 하드코딩
virtual task run_phase(uvm_phase phase);
  phase.raise_objection(this);

  // 리셋
  vif.rst_n = 0;
  @(posedge vif.clk);
  vif.rst_n = 1;

  // 카운트 5회
  vif.enable = 1;
  repeat(5) @(posedge vif.clk);

  // 비활성화
  vif.enable = 0;
  repeat(3) @(posedge vif.clk);

  phase.drop_objection(this);
endtask
```

이 방식에는 세 가지 문제가 있습니다:

**문제 1: 시나리오 변경이 불가능하다**

"카운트 10회" 테스트를 하려면? 드라이버 코드를 수정해야 합니다. "리셋 → 카운트 → 리셋 → 카운트" 패턴은? 또 수정. 테스트 시나리오마다 드라이버를 고치는 것은 비현실적입니다.

**문제 2: 드라이버를 재사용할 수 없다**

드라이버의 본래 역할은 **신호를 구동하는 것**(How)뿐인데, 지금은 **무엇을 구동할지**(What)까지 결정하고 있습니다. 역할이 섞여 있으면 다른 프로젝트에서 재사용할 수 없습니다.

**문제 3: 팀 협업이 어렵다**

실무에서는 드라이버를 만드는 사람과 테스트 시나리오를 작성하는 사람이 다릅니다. 코드가 섞여 있으면 서로의 작업에 영향을 줍니다.

### 6.1.2 해결: What과 How의 분리

```
Chapter 5 방식 (모든 것이 드라이버에)

┌─────────────────────────────────┐
│  Driver                         │
│  ┌───────────────────────────┐  │
│  │ What: 리셋 → 카운트 5회   │  │ ← 시나리오 하드코딩
│  │ How:  vif.enable = 1      │  │ ← 신호 구동
│  └───────────────────────────┘  │
└─────────────────────────────────┘

Chapter 6 방식 (역할 분리)

┌──────────────┐    ┌───────────┐    ┌──────────────┐
│  Sequence     │    │ Sequencer │    │   Driver     │
│  (What)       │───▶│ (중개자)  │───▶│   (How)      │
│  리셋→카운트5 │    │           │    │ vif.enable=1 │
└──────────────┘    └───────────┘    └──────────────┘
```

> **비유**: 택배 시스템을 생각해보세요
> - **Sequence** = 주문서 작성자 — "서울에서 부산으로 5kg 박스를 보내주세요"
> - **Sequence Item** = 주문서 한 장 — 보내는 사람, 받는 사람, 물건 정보
> - **Sequencer** = 택배 회사 본사 — 주문서를 접수하고 배달원에게 전달
> - **Driver** = 배달원 — 주문서대로 물건을 실제로 배달 (신호를 DUT에 구동)
>
> 핵심은 **주문서 작성자가 바뀌어도 배달원은 그대로**라는 점입니다!

### 6.1.3 Sequence-Sequencer-Driver 흐름

전체 데이터 흐름을 정리하면:

```
Sequence-Sequencer-Driver 데이터 흐름:

  Sequence                Sequencer              Driver
┌──────────┐          ┌──────────────┐       ┌──────────────┐
│ body() {  │          │              │       │ run_phase()  │
│   item =  │  ①전달   │   중개자     │ ②전달 │   get_next   │
│   create()│────────▶│   (대기열)   │──────▶│   _item()    │
│   start_  │          │              │       │   신호 구동   │
│   item()  │          │              │ ③완료 │   item_done  │
│   finish_ │◀─ ─ ─ ─ │              │◀──────│   ()         │
│   item()  │  ④다음   │              │       │              │
│ }         │          │              │       │              │
└──────────┘          └──────────────┘       └──────────────┘
```

> **면접 포인트**: "Sequence와 Driver를 분리하는 이유가 무엇인가요?" — **재사용성**과 **유연성**. 같은 Driver로 다양한 Sequence를 실행할 수 있고, 같은 Sequence를 다른 Driver에서도 사용할 수 있습니다.

---

## 6.2 트랜잭션 정의 — uvm_sequence_item

> **이 절의 목표**: DUT와 주고받을 데이터의 구조를 정의하는 방법을 배웁니다. 트랜잭션은 시퀀스 기반 검증의 기본 단위입니다.

### 6.2.1 트랜잭션이란?

트랜잭션(transaction)은 DUT와 한 번 주고받는 데이터의 단위입니다. 택배 비유에서 **주문서 한 장**에 해당합니다.

Chapter 5에서는 `vif.enable = 1`처럼 개별 신호를 직접 다뤘습니다. 이것을 **신호 수준(signal level)**이라 합니다. 시퀀스 기반에서는 신호들을 묶어 하나의 **트랜잭션 수준(transaction level)**으로 추상화합니다:

| 구분 | 신호 수준 (Ch.5) | 트랜잭션 수준 (Ch.6) |
|------|-----------------|---------------------|
| 리셋 | `vif.rst_n = 0` | `item.rst_n = 0` |
| 활성화 | `vif.enable = 1` | `item.enable = 1` |
| 단위 | 개별 신호 | 트랜잭션 객체 |
| 재사용 | 불가 | 가능 |

### 6.2.2 uvm_sequence_item 작성

4비트 카운터의 트랜잭션을 정의해봅시다:

```systemverilog
// 파일: counter_seq_item.sv
// 4비트 카운터용 트랜잭션 정의

class counter_seq_item extends uvm_sequence_item;

  // ① 필드 선언 — DUT 입력에 해당하는 값
  rand bit       rst_n;     // 리셋 (0: 리셋, 1: 해제)
  rand bit       enable;    // 카운터 활성화
  rand int       cycles;    // 이 설정을 유지할 클럭 수

  // ② 출력 필드 — DUT 응답 (모니터가 기록)
  logic [3:0]    count;     // 관찰된 카운트 값

  // ③ 제약 조건 — 합리적인 범위 제한
  constraint c_cycles { cycles inside {[1:20]}; }

  // ④ Factory 등록
  `uvm_object_utils_begin(counter_seq_item)
    `uvm_field_int(rst_n,  UVM_ALL_ON)
    `uvm_field_int(enable, UVM_ALL_ON)
    `uvm_field_int(cycles, UVM_ALL_ON)
    `uvm_field_int(count,  UVM_ALL_ON)
  `uvm_object_utils_end

  // ⑤ 생성자
  function new(string name = "counter_seq_item");
    super.new(name);
  endfunction

  // ⑥ 디버그용 문자열 변환
  function string convert2string();
    return $sformatf("rst_n=%0b enable=%0b cycles=%0d count=%0h",
                     rst_n, enable, cycles, count);
  endfunction

endclass
```

각 부분을 살펴봅시다:

**① `rand` 필드**: `rand` 키워드가 붙은 필드는 `randomize()` 호출 시 랜덤 값이 생성됩니다. DUT에 **입력**할 데이터입니다.

**② 출력 필드**: `rand`가 없는 필드는 DUT의 **응답**을 기록하는 용도입니다. 모니터가 관찰한 값을 여기에 저장합니다.

**③ `constraint`**: 랜덤 값의 범위를 제한합니다. `cycles`를 1~20으로 제한하면 비현실적으로 긴 테스트를 방지합니다. Ch.3에서 배운 constraint 문법 그대로입니다.

**④ Field 매크로**: `uvm_field_int` 매크로로 필드를 등록하면 `print()`, `copy()`, `compare()`, `pack()/unpack()` 기능이 자동으로 제공됩니다. Ch.4에서 배운 `convert2string()`과 함께 디버깅이 쉬워집니다.

> **참고**: `uvm_field_*` 매크로는 편리하지만, 실무에서 성능이 중요한 환경에서는 직접 구현하기도 합니다. 학습 단계에서는 매크로를 사용하는 것이 효율적입니다.

**⑤ 생성자**: `uvm_sequence_item`은 `uvm_object`의 서브클래스이므로, 생성자에 `parent` 인수가 **없습니다** (Ch.4에서 배운 object vs component 차이).

**⑥ `convert2string()`**: 트랜잭션의 내용을 문자열로 출력합니다. 디버깅 시 `uvm_info`와 함께 사용하면 매우 유용합니다.

### 6.2.3 주요 설계 원칙

트랜잭션을 설계할 때 기억할 3가지:

1. **DUT 입력 → `rand` 필드**: 랜덤화할 수 있도록 `rand` 키워드 사용
2. **DUT 출력 → 일반 필드**: 모니터가 기록, 랜덤화 불필요
3. **적절한 constraint**: 유효한 범위를 제한하되, 너무 좁히지 않기

```
트랜잭션 설계 원칙:

                  counter_seq_item
              ┌─────────────────────┐
  DUT 입력    │  rand rst_n         │  ← randomize() 대상
  (구동 값)   │  rand enable        │
              │  rand cycles        │
              ├─────────────────────┤
  DUT 출력    │  count [3:0]        │  ← 모니터가 기록
  (관찰 값)   │                     │
              ├─────────────────────┤
  제약 조건   │  constraint c_cycles│  ← 유효 범위 제한
              │  { cycles∈[1:20] }  │
              └─────────────────────┘
```

> **흔한 실수**: `uvm_sequence_item`을 `uvm_component_utils`로 등록하면 안 됩니다! sequence_item은 `uvm_object`이므로 반드시 `uvm_object_utils`를 사용하세요.

---

## 6.3 시퀀스 작성 — uvm_sequence

> **이 절의 목표**: 트랜잭션을 생성하고 전송하는 시퀀스를 작성합니다. `body()`, `start_item()`/`finish_item()` 패턴이 핵심입니다.

### 6.3.1 시퀀스란?

시퀀스(sequence)는 **트랜잭션의 시나리오**입니다. 택배 비유에서 "이 순서대로 주문서를 보내세요"라는 지시서에 해당합니다.

시퀀스의 핵심 메서드는 `body()`입니다. 시퀀스가 실행되면 `body()`가 자동으로 호출되고, 여기서 트랜잭션을 생성하고 전송합니다.

### 6.3.2 첫 번째 시퀀스: 리셋 시퀀스

가장 간단한 시퀀스부터 만들어봅시다 — DUT를 리셋하는 시퀀스:

```systemverilog
// 파일: counter_reset_seq.sv
// 리셋 시퀀스: DUT를 리셋 상태로 만듦

class counter_reset_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_reset_seq)

  function new(string name = "counter_reset_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_seq_item item;

    // ① 트랜잭션 생성 (Factory 사용)
    item = counter_seq_item::type_id::create("item");

    // ② 시퀀서에게 전송 시작 알림
    start_item(item);

    // ③ 트랜잭션 값 설정
    item.rst_n  = 0;       // 리셋 활성화
    item.enable = 0;
    item.cycles = 2;       // 2 클럭 동안 유지

    // ④ 시퀀서에게 전송 완료 알림
    finish_item(item);

    `uvm_info(get_type_name(), "Reset sequence completed", UVM_MEDIUM)
  endtask

endclass
```

**`start_item()` / `finish_item()` 이해하기**:

이 두 메서드가 시퀀스의 핵심입니다:

| 단계 | 메서드 | 하는 일 |
|------|--------|--------|
| 1 | `create()` | 트랜잭션 객체 생성 (빈 주문서 준비) |
| 2 | `start_item(item)` | 시퀀서에게 "보낼 거 있어요" 알림 (드라이버가 준비될 때까지 대기) |
| 3 | 값 설정 / `randomize()` | 트랜잭션에 실제 데이터 기록 (주문서 작성) |
| 4 | `finish_item(item)` | 트랜잭션을 드라이버에게 전달, 처리 완료까지 대기 (주문서 접수) |

> **왜 start_item 다음에 값을 설정하나요?**: `start_item()`은 드라이버가 이전 트랜잭션 처리를 끝낼 때까지 대기합니다. 이 대기 후에 값을 설정해야 **가장 최신 상태**를 반영할 수 있습니다. 이것은 UVM의 **late randomization** 패턴입니다.

> **안심하세요**: `start_item()` → 값 설정 → `finish_item()` 이 3단계 패턴만 외우면 됩니다. 모든 시퀀스가 이 패턴을 따릅니다. 지금은 "왜?" 보다 "이렇게 쓴다"를 먼저 익히세요.

### 6.3.3 두 번째 시퀀스: 카운트 시퀀스

이번에는 랜덤화를 활용하는 시퀀스를 만들어봅시다:

```systemverilog
// 파일: counter_count_seq.sv
// 카운트 시퀀스: enable 활성화 후 N회 카운트

class counter_count_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_count_seq)

  // 시퀀스 레벨 파라미터
  rand int num_transactions;
  constraint c_num { num_transactions inside {[3:10]}; }

  function new(string name = "counter_count_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_seq_item item;

    `uvm_info(get_type_name(),
      $sformatf("Starting count sequence with %0d transactions", num_transactions),
      UVM_MEDIUM)

    // 여러 트랜잭션을 순차적으로 전송
    for (int i = 0; i < num_transactions; i++) begin
      item = counter_seq_item::type_id::create($sformatf("item_%0d", i));
      start_item(item);

      // ⭐ randomize()로 값 설정 + constraint로 범위 제한
      if (!item.randomize() with {
        rst_n  == 1;             // 리셋 해제 상태
        enable == 1;             // 카운트 활성화
        cycles inside {[1:5]};   // 1~5 클럭
      }) begin
        `uvm_fatal(get_type_name(), "Randomization failed!")
      end

      finish_item(item);
      `uvm_info(get_type_name(),
        $sformatf("  [%0d/%0d] %s", i+1, num_transactions, item.convert2string()),
        UVM_HIGH)
    end
  endtask

endclass
```

**핵심 패턴: `randomize() with {}`**

`start_item()` 다음에 `randomize() with {}` 구문으로:
- 기본 constraint (클래스에 정의된 `c_cycles`)와
- 추가 constraint (inline `with {}`)를
동시에 적용합니다.

이렇게 하면 **시퀀스마다 다른 제약 조건**을 줄 수 있어 유연합니다:

```systemverilog
// 리셋 시퀀스: 항상 rst_n=0
item.randomize() with { rst_n == 0; };

// 카운트 시퀀스: 항상 rst_n=1, enable=1
item.randomize() with { rst_n == 1; enable == 1; };

// 완전 랜덤 시퀀스: 제약 없음
item.randomize();
```

### 6.3.4 `uvm_do 매크로 — 간편 표기

UVM은 `start_item`/`finish_item` 패턴을 간단히 쓸 수 있는 매크로를 제공합니다:

```systemverilog
// 명시적 패턴 (추천)
item = counter_seq_item::type_id::create("item");
start_item(item);
item.randomize() with { rst_n == 1; enable == 1; };
finish_item(item);

// `uvm_do 매크로 (간편)
`uvm_do(item)                          // create + start + randomize + finish

// `uvm_do_with 매크로 (간편 + 제약)
`uvm_do_with(item, { rst_n == 1; enable == 1; })
```

| 방식 | 장점 | 단점 |
|------|------|------|
| 명시적 패턴 | 동작이 명확, 디버깅 쉬움 | 코드가 길다 |
| `uvm_do 매크로 | 코드가 짧다 | 내부 동작 숨김, late randomization 불가 |

> **면접 포인트**: "uvm_do와 start_item/finish_item의 차이는?" — `uvm_do`는 `create + start_item + randomize + finish_item`을 한 줄로 수행합니다. 명시적 패턴은 **start_item 후에 randomize**할 수 있어 late randomization이 가능합니다. 실무에서는 명시적 패턴을 더 많이 사용합니다.

### 6.3.5 시퀀스 조합: 마스터 시퀀스

여러 시퀀스를 순서대로 실행하는 마스터 시퀀스를 만들 수 있습니다:

```systemverilog
// 파일: counter_master_seq.sv
// 마스터 시퀀스: 리셋 → 카운트 순서로 실행

class counter_master_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_master_seq)

  function new(string name = "counter_master_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_reset_seq reset_seq;
    counter_count_seq count_seq;

    // ① 리셋 시퀀스 실행
    `uvm_info(get_type_name(), "=== Phase 1: Reset ===", UVM_MEDIUM)
    reset_seq = counter_reset_seq::type_id::create("reset_seq");
    reset_seq.start(m_sequencer);  // 같은 시퀀서에서 실행

    // ② 카운트 시퀀스 실행
    `uvm_info(get_type_name(), "=== Phase 2: Count ===", UVM_MEDIUM)
    count_seq = counter_count_seq::type_id::create("count_seq");
    count_seq.num_transactions = 5;
    count_seq.start(m_sequencer);

    `uvm_info(get_type_name(), "=== Master sequence completed ===", UVM_MEDIUM)
  endtask

endclass
```

**핵심**: 서브 시퀀스의 `start()` 호출 시 `m_sequencer`를 전달합니다. `m_sequencer`는 현재 시퀀스가 실행 중인 시퀀서를 가리키는 핸들로, 상위 시퀀스에서 `start(sequencer)` 호출 시 **자동으로 설정**됩니다. 직접 할당할 필요가 없습니다.

```
시퀀스 조합 구조:

  counter_master_seq
  ┌──────────────────────────────────────┐
  │  body() {                            │
  │    ┌──────────────────┐              │
  │    │ reset_seq.start()│ → 리셋 실행  │
  │    └──────────────────┘              │
  │              ↓                       │
  │    ┌──────────────────┐              │
  │    │ count_seq.start()│ → 카운트 실행│
  │    └──────────────────┘              │
  │  }                                   │
  └──────────────────────────────────────┘
                   │
                   ▼
             m_sequencer (같은 시퀀서)
```

---

## 6.4 시퀀서와 드라이버 연결

> **이 절의 목표**: 시퀀서의 역할을 이해하고, 드라이버가 시퀀서로부터 트랜잭션을 받아 처리하는 패턴을 배웁니다.

### 6.4.1 시퀀서 (uvm_sequencer)

시퀀서는 시퀀스와 드라이버 사이의 **중개자**입니다. 택배 비유에서 택배 회사 본사에 해당합니다:

```systemverilog
// 파일: counter_sequencer.sv
// 시퀀서: 대부분의 경우 이렇게 간단합니다!

class counter_sequencer extends uvm_sequencer #(counter_seq_item);
  `uvm_component_utils(counter_sequencer)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
endclass
```

> **시퀀서가 이렇게 간단한 이유**: `uvm_sequencer` 기본 클래스가 대부분의 기능을 이미 제공하기 때문입니다. 시퀀스 큐잉, 중재(arbitration), 드라이버 연결 등이 모두 내장되어 있습니다. 사용자는 **트랜잭션 타입만 지정**하면 됩니다.

### 6.4.2 드라이버 리팩토링: get_next_item()/item_done()

Chapter 5의 드라이버를 시퀀스 기반으로 리팩토링합니다. 핵심 변화는 **시퀀서로부터 트랜잭션을 받아서** 신호를 구동하는 것입니다:

```systemverilog
// 파일: counter_driver.sv
// Chapter 6 방식: 시퀀서에서 트랜잭션을 받아 신호 구동

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

  // ⭐ 핵심 변경: 무한 루프로 트랜잭션을 계속 받아 처리
  virtual task run_phase(uvm_phase phase);
    counter_seq_item item;

    forever begin
      // ① 시퀀서에서 다음 트랜잭션 가져오기 (대기)
      seq_item_port.get_next_item(item);

      // ② 트랜잭션 내용대로 신호 구동
      drive_item(item);

      // ③ 처리 완료 알림
      seq_item_port.item_done();
    end
  endtask

  // 실제 신호 구동 로직
  virtual task drive_item(counter_seq_item item);
    vif.rst_n  <= item.rst_n;
    vif.enable <= item.enable;
    repeat(item.cycles) @(posedge vif.clk);
  endtask

endclass
```

**핵심 패턴: `get_next_item()` → 구동 → `item_done()`**

| 단계 | 메서드 | 하는 일 |
|------|--------|--------|
| 1 | `get_next_item(item)` | 시퀀서에서 트랜잭션을 받아옴 (없으면 대기) |
| 2 | `drive_item(item)` | 트랜잭션 내용대로 DUT 신호 구동 |
| 3 | `item_done()` | 처리 완료를 시퀀서에게 알림 |

> **`forever` 루프가 중요한 이유**: 드라이버는 시뮬레이션이 끝날 때까지 계속 트랜잭션을 받아 처리해야 합니다. 시퀀스가 끝나면 `get_next_item()`에서 자연스럽게 대기합니다.

> **드라이버에 `raise_objection`이 없는 이유**: objection은 시뮬레이션 종료를 제어합니다. 시퀀스 기반에서는 **test 클래스**가 `raise_objection`/`drop_objection`을 관리하므로, 드라이버는 시퀀서에서 트랜잭션을 받아 처리하는 역할만 합니다.

> **주의**: `get_next_item()`과 `item_done()`은 반드시 **쌍으로** 호출해야 합니다. `item_done()`을 빠뜨리면 시퀀서가 영원히 대기합니다!

### 6.4.3 seq_item_port — 드라이버와 시퀀서의 연결

`seq_item_port`는 `uvm_driver` 기본 클래스에 이미 선언되어 있습니다. agent의 `connect_phase`에서 드라이버와 시퀀서를 연결합니다:

```systemverilog
// agent의 connect_phase에서 연결
virtual function void connect_phase(uvm_phase phase);
  super.connect_phase(phase);
  drv.seq_item_port.connect(sqr.seq_item_export);
endfunction
```

> **이 한 줄이 전부입니다!** `drv.seq_item_port.connect(sqr.seq_item_export)` — 이 연결 덕분에 시퀀스가 `start_item()`/`finish_item()`으로 보낸 트랜잭션이 드라이버의 `get_next_item()`으로 전달됩니다. 내부 동작(TLM 포트)은 Chapter 7에서 자세히 다룹니다. 지금은 이 **한 줄 연결 패턴**만 기억하세요.

### 6.4.4 시퀀스 실행: test에서 start() 호출

시퀀스는 test 클래스의 `run_phase`에서 시작합니다:

```systemverilog
// test의 run_phase에서 시퀀스 실행
virtual task run_phase(uvm_phase phase);
  counter_master_seq master_seq;

  phase.raise_objection(this);

  master_seq = counter_master_seq::type_id::create("master_seq");
  master_seq.start(env.agent.sqr);  // ⭐ 시퀀서를 지정하여 실행

  phase.drop_objection(this);
endtask
```

**`start()` 메서드의 인수는 시퀀서**입니다. 이것이 시퀀스와 시퀀서를 연결하는 마지막 고리입니다.

```
전체 연결 구조:

  Test.run_phase
       │
       │ seq.start(sqr)        ← 시퀀스를 시퀀서에서 실행
       ▼
  ┌──────────┐   start_item/   ┌───────────┐  get_next_item  ┌─────────┐
  │ Sequence │──finish_item──▶│ Sequencer │──────────────▶│ Driver  │
  │ (What)   │                 │ (중개자)  │                  │ (How)   │
  └──────────┘                 └───────────┘   item_done     └─────────┘
                                               ◀──────────
```

> **면접 포인트**: "시퀀스를 실행하는 3단계를 설명하세요" —
> 1. 시퀀스 객체 생성 (`type_id::create`)
> 2. 시퀀서 지정하여 실행 (`seq.start(sequencer)`)
> 3. 시퀀스의 `body()`가 자동 호출되어 트랜잭션 전송

---

## 6.5 종합: 시퀀스 기반 테스트벤치

> **이 절의 목표**: Chapter 5의 테스트벤치를 시퀀스 기반으로 리팩토링합니다. 완전한 코드를 단계별로 조립합니다.

### 6.5.1 Before → After 비교

```
Chapter 5 vs Chapter 6 구조 비교:

Chapter 5 (하드코딩)              Chapter 6 (시퀀스 기반)
┌──────────────┐                 ┌──────────────┐
│    Test      │                 │    Test      │
│ (run_phase   │                 │  seq.start() │
│  없음)       │                 │              │
└──────────────┘                 └──────┬───────┘
                                        │ start(sqr)
                                        ▼
                                 ┌──────────────┐
                                 │  Sequence    │
                                 │  body() {    │
                                 │   start_item │
                                 │   finish_item│
                                 │  }           │
                                 └──────┬───────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │  Sequencer   │
                                 └──────┬───────┘
                                        │
┌──────────────┐                 ┌──────┴───────┐
│   Driver     │                 │   Driver     │
│ (시나리오 +  │                 │(get_next_item│
│  신호 구동)  │                 │ → 신호 구동) │
└──────────────┘                 └──────────────┘
```

### 6.5.2 완전한 코드

이제 모든 부분을 합쳐봅시다. 이 코드는 Chapter 5의 테스트벤치를 시퀀스 기반으로 리팩토링한 것입니다:

**[예제 6-1] 시퀀스 기반 완전한 UVM 테스트벤치**

```systemverilog
// ================================================================
// [예제 6-1] 시퀀스 기반 UVM 테스트벤치
// 파일: counter_seq_tb.sv
// Chapter 5의 테스트벤치를 시퀀스 기반으로 리팩토링
// ================================================================

// ---- Step 1: Interface (Ch.5와 동일) ----
interface counter_if(input logic clk);
  logic       rst_n;
  logic       enable;
  logic [3:0] count;
endinterface

// ---- Step 2: DUT (Ch.5와 동일) ----
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

// ---- Step 3: 트랜잭션 (NEW!) ----
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

// ---- Step 4: 리셋 시퀀스 (NEW!) ----
class counter_reset_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_reset_seq)

  function new(string name = "counter_reset_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_seq_item item;
    item = counter_seq_item::type_id::create("item");
    start_item(item);
    item.rst_n  = 0;
    item.enable = 0;
    item.cycles = 2;
    finish_item(item);
    `uvm_info(get_type_name(), "Reset done", UVM_MEDIUM)
  endtask
endclass

// ---- Step 5: 카운트 시퀀스 (NEW!) ----
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
      if (!item.randomize() with {
        rst_n  == 1;
        enable == 1;
        cycles inside {[1:5]};
      }) `uvm_fatal(get_type_name(), "Randomization failed!")
      finish_item(item);
      `uvm_info(get_type_name(),
        $sformatf("[%0d/%0d] %s", i+1, num_transactions, item.convert2string()),
        UVM_HIGH)
    end
  endtask
endclass

// ---- Step 6: 마스터 시퀀스 (NEW!) ----
class counter_master_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_master_seq)

  function new(string name = "counter_master_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_reset_seq reset_seq;
    counter_count_seq count_seq;

    `uvm_info(get_type_name(), "=== Phase 1: Reset ===", UVM_MEDIUM)
    reset_seq = counter_reset_seq::type_id::create("reset_seq");
    reset_seq.start(m_sequencer);

    `uvm_info(get_type_name(), "=== Phase 2: Count ===", UVM_MEDIUM)
    count_seq = counter_count_seq::type_id::create("count_seq");
    count_seq.num_transactions = 5;
    count_seq.start(m_sequencer);

    `uvm_info(get_type_name(), "=== Master sequence done ===", UVM_MEDIUM)
  endtask
endclass

// ---- Step 7: 시퀀서 (NEW!) ----
class counter_sequencer extends uvm_sequencer #(counter_seq_item);
  `uvm_component_utils(counter_sequencer)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
endclass

// ---- Step 8: 드라이버 (리팩토링!) ----
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
    forever begin
      seq_item_port.get_next_item(item);
      drive_item(item);
      seq_item_port.item_done();
    end
  endtask

  virtual task drive_item(counter_seq_item item);
    vif.rst_n  <= item.rst_n;
    vif.enable <= item.enable;
    repeat(item.cycles) @(posedge vif.clk);
  endtask
endclass

// ---- Step 9: 모니터 (Ch.5와 동일) ----
class counter_monitor extends uvm_monitor;
  `uvm_component_utils(counter_monitor)

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
    forever begin
      @(posedge vif.clk);
      #1;  // 신호 안정화 대기 (Ch.7에서 clocking block으로 개선)
      `uvm_info(get_type_name(),
        $sformatf("rst_n=%0b enable=%0b count=%0d",
                  vif.rst_n, vif.enable, vif.count),
        UVM_HIGH)
    end
  endtask
endclass

// ---- Step 10: 에이전트 (시퀀서 추가!) ----
class counter_agent extends uvm_agent;
  `uvm_component_utils(counter_agent)

  counter_sequencer sqr;   // ⭐ 시퀀서 추가
  counter_driver    drv;
  counter_monitor   mon;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    sqr = counter_sequencer::type_id::create("sqr", this);  // ⭐
    drv = counter_driver::type_id::create("drv", this);
    mon = counter_monitor::type_id::create("mon", this);
  endfunction

  // ⭐ 시퀀서와 드라이버 연결
  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    drv.seq_item_port.connect(sqr.seq_item_export);
  endfunction
endclass

// ---- Step 11: 환경 (Ch.5와 유사) ----
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

// ---- Step 12: 테스트 (시퀀스 실행!) ----
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

  // ⭐ 핵심 변경: 시퀀스를 생성하고 시퀀서에서 실행
  virtual task run_phase(uvm_phase phase);
    counter_master_seq seq;

    phase.raise_objection(this);

    seq = counter_master_seq::type_id::create("seq");
    seq.start(env.agent.sqr);  // 시퀀서 지정

    #100;  // 추가 관찰 시간
    phase.drop_objection(this);
  endtask
endclass

// ---- Step 13: Top 모듈 (Ch.5와 유사) ----
module top;
  logic clk;

  // 클럭 생성
  initial clk = 0;
  always #5 clk = ~clk;

  // Interface & DUT
  counter_if vif(clk);
  counter dut(
    .clk(clk),
    .rst_n(vif.rst_n),
    .enable(vif.enable),
    .count(vif.count)
  );

  initial begin
    // Virtual interface를 config_db에 등록
    uvm_config_db#(virtual counter_if)::set(null, "*", "vif", vif);
    run_test("counter_test");
  end

  // 파형 덤프
  initial begin
    $dumpfile("counter_seq.vcd");
    $dumpvars(0, top);
  end
endmodule
```

### 6.5.3 Ch.5 대비 변경 사항 정리

| 항목 | Chapter 5 | Chapter 6 |
|------|-----------|-----------|
| 트랜잭션 | 없음 (직접 신호) | `counter_seq_item` 클래스 |
| 시나리오 위치 | 드라이버 안에 하드코딩 | `counter_sequence` 클래스로 분리 |
| 드라이버 역할 | What + How | **How만** (`get_next_item` → 구동) |
| 시퀀서 | 없음 | `counter_sequencer` 추가 |
| 테스트 변경 | 드라이버 코드 수정 | **새 시퀀스 작성**만 하면 됨 |
| 연결 | 없음 | `connect_phase`에서 `seq_item_port` 연결 |
| 재사용 | 불가능 | **드라이버 재사용 가능** |

### 6.5.4 다양한 테스트 만들기

시퀀스 기반의 가장 큰 장점: **드라이버를 수정하지 않고** 새 시퀀스만 만들면 새 테스트가 됩니다:

```systemverilog
// 테스트 2: 오버플로 테스트 — 16회 이상 카운트
class counter_overflow_test extends counter_test;
  `uvm_component_utils(counter_overflow_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual task run_phase(uvm_phase phase);
    counter_reset_seq reset_seq;
    counter_count_seq count_seq;

    phase.raise_objection(this);

    // 리셋
    reset_seq = counter_reset_seq::type_id::create("reset_seq");
    reset_seq.start(env.agent.sqr);

    // 20회 카운트 — 오버플로 발생!
    count_seq = counter_count_seq::type_id::create("count_seq");
    count_seq.num_transactions = 20;
    count_seq.start(env.agent.sqr);

    #50;
    phase.drop_objection(this);
  endtask
endclass

// 테스트 3: 리셋 반복 테스트 — 카운트 중 리셋
class counter_reset_during_count_test extends counter_test;
  `uvm_component_utils(counter_reset_during_count_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual task run_phase(uvm_phase phase);
    counter_reset_seq reset_seq;
    counter_count_seq count_seq;

    phase.raise_objection(this);

    // 리셋 → 카운트 → 리셋 → 카운트 (반복)
    for (int round = 0; round < 3; round++) begin
      `uvm_info(get_type_name(), $sformatf("=== Round %0d ===", round+1), UVM_MEDIUM)

      reset_seq = counter_reset_seq::type_id::create("reset_seq");
      reset_seq.start(env.agent.sqr);

      count_seq = counter_count_seq::type_id::create("count_seq");
      count_seq.num_transactions = 3;
      count_seq.start(env.agent.sqr);
    end

    #50;
    phase.drop_objection(this);
  endtask
endclass
```

> **성취감 포인트**: 드라이버 코드를 **한 줄도 수정하지 않고** 3가지 테스트를 만들었습니다! 이것이 시퀀스 기반 검증의 힘입니다. 실무에서는 이런 방식으로 수십~수백 개의 테스트 시나리오를 만듭니다.

### 6.5.5 시뮬레이션 실행

```bash
# 컴파일 및 실행 (기본 테스트)
vcs -sverilog -ntb_opts uvm counter_seq_tb.sv
./simv +UVM_TESTNAME=counter_test

# 오버플로 테스트 실행 — 드라이버 수정 없이!
./simv +UVM_TESTNAME=counter_overflow_test

# 리셋 반복 테스트 실행
./simv +UVM_TESTNAME=counter_reset_during_count_test
```

> **실무 팁**: `+UVM_TESTNAME`으로 테스트를 선택하는 패턴은 실무에서도 동일합니다. 회사의 regression 스크립트는 이 방식으로 수백 개 테스트를 자동 실행합니다.

예상 출력:

```
UVM_INFO @ 0: reporter [RNTST] Running test counter_test...
UVM_INFO counter_master_seq [counter_master_seq] === Phase 1: Reset ===
UVM_INFO counter_reset_seq [counter_reset_seq] Reset done
UVM_INFO counter_master_seq [counter_master_seq] === Phase 2: Count ===
UVM_INFO counter_master_seq [counter_master_seq] === Master sequence done ===
UVM_INFO @ 200: reporter [TEST_DONE] ** UVM TEST PASSED **
```

---

## 6.6 체크포인트

### 셀프 체크

아래 질문에 스스로 답해보세요. 답이 바로 나오지 않으면 해당 섹션을 다시 읽어보세요:

**1. 왜 시퀀스가 필요한가?** (6.1)
<details>
<summary>정답 확인</summary>
Chapter 5 방식은 테스트 시나리오가 드라이버에 하드코딩되어 있어 변경, 재사용, 팀 협업이 어렵습니다. 시퀀스를 사용하면 "무엇을(What)"과 "어떻게(How)"를 분리하여, 드라이버를 수정하지 않고 새 시나리오를 추가할 수 있습니다.
</details>

**2. uvm_sequence_item은 uvm_object의 서브클래스입니다. 이것이 의미하는 것은?** (6.2)
<details>
<summary>정답 확인</summary>
uvm_object이므로 ① 컴포넌트 트리에 속하지 않고 ② 생성자에 parent가 없으며 ③ Factory에 `uvm_object_utils`로 등록합니다. `uvm_component_utils`를 사용하면 안 됩니다.
</details>

**3. start_item() 다음에 randomize()를 호출하는 이유는?** (6.3)
<details>
<summary>정답 확인</summary>
start_item()은 드라이버가 이전 트랜잭션 처리를 끝낼 때까지 대기합니다. 대기 후에 randomize()를 호출해야 가장 최신 상태를 반영할 수 있습니다. 이것을 "late randomization" 패턴이라 합니다.
</details>

**4. 드라이버의 get_next_item()과 item_done()을 쌍으로 호출해야 하는 이유는?** (6.4)
<details>
<summary>정답 확인</summary>
get_next_item()으로 트랜잭션을 가져온 후 item_done()으로 완료를 알려야 시퀀서가 다음 트랜잭션을 전달할 수 있습니다. item_done()을 빠뜨리면 시퀀서가 영원히 대기(hang)합니다.
</details>

**5. `uvm_do_with 매크로와 명시적 start_item/finish_item 패턴의 차이는?** (6.3)
<details>
<summary>정답 확인</summary>
`uvm_do_with는 create+start_item+randomize+finish_item을 한 줄로 수행합니다. 명시적 패턴은 start_item 후에 randomize하므로 late randomization이 가능합니다. 실무에서는 명시적 패턴을 더 많이 사용합니다.
</details>

**6. 시퀀스 기반에서 새 테스트 시나리오를 추가하려면?** (6.5)
<details>
<summary>정답 확인</summary>
새 시퀀스 클래스를 만들거나, 새 테스트 클래스에서 기존 시퀀스를 다른 순서/파라미터로 조합합니다. 드라이버 코드를 수정할 필요가 없습니다.
</details>

---

### 연습문제

**[실습 6-1] 토글 시퀀스 만들기 (쉬움)** — 약 10분

enable을 0→1→0→1로 토글하는 시퀀스를 만드세요:

```systemverilog
// 힌트: 4개의 트랜잭션을 순서대로 전송
// item[0]: enable=0, cycles=2
// item[1]: enable=1, cycles=3
// item[2]: enable=0, cycles=2
// item[3]: enable=1, cycles=3

class counter_toggle_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_toggle_seq)

  function new(string name = "counter_toggle_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_seq_item item;
    // 여기에 코드를 작성하세요
    // 힌트: for 루프에서 i%2로 enable 토글
    for (int i = 0; i < 4; i++) begin
      item = counter_seq_item::type_id::create($sformatf("item_%0d", i));
      start_item(item);
      // TODO: rst_n=1, enable=?, cycles=?
      finish_item(item);
    end
  endtask
endclass
```

**정답**:
<details>
<summary>정답 확인</summary>

```systemverilog
virtual task body();
  counter_seq_item item;
  for (int i = 0; i < 4; i++) begin
    item = counter_seq_item::type_id::create($sformatf("item_%0d", i));
    start_item(item);
    item.rst_n  = 1;
    item.enable = (i % 2);      // 0, 1, 0, 1 토글
    item.cycles = (i % 2) ? 3 : 2;  // enable일 때 3클럭, 아닐 때 2클럭
    finish_item(item);
  end
endtask
```
</details>

---

**[실습 6-2] 랜덤 스트레스 시퀀스 (보통)** — 약 15분

완전히 랜덤한 트랜잭션을 N회 전송하는 스트레스 시퀀스를 만드세요. `rst_n`, `enable`, `cycles` 모두 랜덤이어야 합니다:

```systemverilog
// 요구사항:
// 1. num_items 파라미터로 트랜잭션 수 지정 (기본값 20)
// 2. 모든 필드를 randomize()로 생성
// 3. 각 트랜잭션 전송 후 convert2string()으로 로그 출력
// 4. 시작과 끝에 UVM_MEDIUM 레벨 로그 출력

class counter_stress_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_stress_seq)

  int num_items = 20;

  function new(string name = "counter_stress_seq");
    super.new(name);
  endfunction

  virtual task body();
    // 여기에 코드를 작성하세요
  endtask
endclass
```

**정답**:
<details>
<summary>정답 확인</summary>

```systemverilog
virtual task body();
  counter_seq_item item;

  `uvm_info(get_type_name(),
    $sformatf("Starting stress sequence with %0d items", num_items), UVM_MEDIUM)

  for (int i = 0; i < num_items; i++) begin
    item = counter_seq_item::type_id::create($sformatf("item_%0d", i));
    start_item(item);
    if (!item.randomize())
      `uvm_fatal(get_type_name(), "Randomization failed!")
    finish_item(item);
    `uvm_info(get_type_name(),
      $sformatf("[%0d/%0d] %s", i+1, num_items, item.convert2string()), UVM_HIGH)
  end

  `uvm_info(get_type_name(), "Stress sequence completed", UVM_MEDIUM)
endtask
```
</details>

---

**[실습 6-3] 시퀀스 조합 테스트 (도전)** — 약 20분

리셋 → 스트레스 → 리셋 → 카운트 순서의 종합 테스트를 만드세요:

```systemverilog
// 요구사항:
// 1. counter_test를 상속받는 새 테스트 클래스
// 2. run_phase에서 4단계 시퀀스를 순서대로 실행:
//    Phase 1: 리셋 (counter_reset_seq)
//    Phase 2: 스트레스 10회 (실습 6-2의 counter_stress_seq)
//    Phase 3: 리셋 (counter_reset_seq)
//    Phase 4: 정상 카운트 5회 (counter_count_seq)
// 3. 각 Phase 시작 시 UVM_MEDIUM 레벨 로그

class counter_comprehensive_test extends counter_test;
  `uvm_component_utils(counter_comprehensive_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual task run_phase(uvm_phase phase);
    // 여기에 코드를 작성하세요
  endtask
endclass
```

**정답**:
<details>
<summary>정답 확인</summary>

```systemverilog
virtual task run_phase(uvm_phase phase);
  counter_reset_seq  reset_seq;
  counter_stress_seq stress_seq;
  counter_count_seq  count_seq;

  phase.raise_objection(this);

  // Phase 1: 리셋
  `uvm_info(get_type_name(), "=== Phase 1: Initial Reset ===", UVM_MEDIUM)
  reset_seq = counter_reset_seq::type_id::create("reset_seq");
  reset_seq.start(env.agent.sqr);

  // Phase 2: 스트레스
  `uvm_info(get_type_name(), "=== Phase 2: Stress Test ===", UVM_MEDIUM)
  stress_seq = counter_stress_seq::type_id::create("stress_seq");
  stress_seq.num_items = 10;
  stress_seq.start(env.agent.sqr);

  // Phase 3: 리셋
  `uvm_info(get_type_name(), "=== Phase 3: Mid Reset ===", UVM_MEDIUM)
  reset_seq = counter_reset_seq::type_id::create("reset_seq2");
  reset_seq.start(env.agent.sqr);

  // Phase 4: 정상 카운트
  `uvm_info(get_type_name(), "=== Phase 4: Normal Count ===", UVM_MEDIUM)
  count_seq = counter_count_seq::type_id::create("count_seq");
  count_seq.num_transactions = 5;
  count_seq.start(env.agent.sqr);

  #50;
  phase.drop_objection(this);
endtask
```
</details>

---

### 흔한 에러와 해결

| 에러 메시지 | 원인 | 해결 |
|------------|------|------|
| `Null object access` (sequence) | 시퀀스 `start()` 시 시퀀서가 null | `env.agent.sqr` 경로 확인, `build_phase`에서 시퀀서 생성 확인 |
| `item_done() not called` | 드라이버에서 `item_done()` 누락 | `get_next_item()` 후 반드시 `item_done()` 호출 |
| `Sequencer has no driver` | `connect_phase`에서 연결 누락 | `drv.seq_item_port.connect(sqr.seq_item_export)` 확인 |
| `Randomization failed` | constraint 충돌 | inline constraint와 클래스 constraint 간 충돌 확인 |
| `uvm_component_utils` 사용 | sequence_item에 잘못된 매크로 | `uvm_object_utils` 또는 `uvm_object_utils_begin` 사용 |

### 용어 정리

| 용어 | 영어 | 설명 |
|------|------|------|
| 트랜잭션 | Transaction | DUT와 한 번 주고받는 데이터 단위 |
| 시퀀스 아이템 | Sequence Item | 트랜잭션 클래스 (uvm_sequence_item) |
| 시퀀스 | Sequence | 트랜잭션 생성 시나리오 (uvm_sequence) |
| 시퀀서 | Sequencer | 시퀀스와 드라이버의 중개자 (uvm_sequencer) |
| 바디 | body() | 시퀀스의 핵심 실행 메서드 |
| 레이트 랜덤화 | Late Randomization | start_item 후 randomize하는 패턴 |
| 마스터 시퀀스 | Master Sequence | 여러 서브 시퀀스를 조합하는 시퀀스 |

### 다음 챕터 예고

Chapter 7에서는 지금 "마법처럼" 연결한 `seq_item_port`/`seq_item_export`의 내부 동작을 다룹니다. **TLM(Transaction Level Modeling)** 포트의 개념과 드라이버/모니터의 심화 기능을 배웁니다.
