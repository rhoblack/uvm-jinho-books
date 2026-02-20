# Chapter 15: 면접 준비 & 포트폴리오

> **학습 목표**
> - **UVM 면접 빈출 질문 30선**을 이해하고 모범 답안을 준비할 수 있다
> - **코드 리뷰 면접**에서 UVM 코드의 문제를 찾고 개선안을 제시할 수 있다
> - **포트폴리오 프로젝트**를 Ch.11~14 APB 검증 환경을 기반으로 구성할 수 있다
> - **이력서와 GitHub**에 검증 엔지니어 역량을 효과적으로 보여줄 수 있다
> - **팹리스 검증 엔지니어** 취업 프로세스와 면접 전략을 이해할 수 있다

> **선수 지식**: 이 챕터는 Ch.1~14 전체를 참조합니다. 특히 Ch.4(Factory/Phase), Ch.6~7(Sequence/Driver/Monitor), Ch.8(Scoreboard), Ch.11~14(APB 검증 환경)가 면접과 포트폴리오의 핵심 소재입니다.

---

## 15.1 팹리스 검증 엔지니어 취업 로드맵

> **이 절의 목표**: 팹리스 검증 엔지니어가 실제로 어떤 일을 하는지, 채용 프로세스는 어떻게 진행되는지 이해합니다.

### 15.1.1 팹리스 검증팀의 하루

Ch.1~14에서 UVM 기술을 배웠습니다. 그런데 **실제로 출근하면 뭘 할까요?** 팹리스 검증 엔지니어의 전형적인 하루를 봅시다:

| 시간 | 활동 | UVM과의 연결 |
|------|------|-------------|
| 09:00 | 출근, 밤새 돌린 리그레션 결과 확인 | 수백 개 테스트 자동 실행 결과 분석 |
| 09:30 | 팀 스탠드업 미팅 | 커버리지 진행률, 발견된 버그 공유 |
| 10:00 | 커버리지 홀(hole) 분석 | Ch.14에서 배운 커버리지 리포트 분석 |
| 11:00 | 새 테스트 시나리오 작성 | Ch.6 시퀀스, Ch.13 가상 시퀀스 |
| 13:00 | 발견된 버그 분석 및 리포트 | Ch.10 디버깅, 파형 분석 |
| 14:00 | 설계팀과 버그 논의 미팅 | 프로토콜 이해, 어서션 결과 공유 |
| 15:00 | 새 IP 블록의 테스트벤치 구축 | Ch.5~8 에이전트, 스코어보드 |
| 16:00 | 코드 리뷰 (동료 코드 검토) | 이 챕터 15.3에서 연습! |
| 17:00 | 리그레션 설정 후 퇴근 | 밤새 자동 실행될 테스트 세트 |

> 💡 **핵심**: 검증 엔지니어의 업무는 크게 **"테스트 작성"**, **"커버리지 분석"**, **"버그 디버깅"** 세 가지입니다. Ch.1~14에서 배운 것이 바로 이 업무를 하기 위한 기술입니다.

**검증 엔지니어가 되면 좋은 점:**

| 장점 | 설명 |
|------|------|
| **높은 수요** | 설계 대비 검증 인력 비율 2:1~3:1 — 항상 인력 부족 |
| **체계적 사고력** | "어떻게 하면 버그를 찾을까?"라는 창의적 문제 해결 |
| **설계 이해** | 하드웨어 전체를 이해하게 됨 (검증이 곧 설계 이해) |
| **글로벌 기회** | UVM은 전 세계 표준 — 해외 취업 가능성 |

### 15.1.2 채용 프로세스 이해하기

팹리스 검증 엔지니어 채용은 보통 다음 과정을 거칩니다:

```
팹리스 검증 엔지니어 채용 프로세스

┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 1. 서류  │───▶│ 2. 코딩  │───▶│ 3. 1차   │───▶│ 4. 2차   │───▶│ 5. 처우  │
│   전형   │    │   테스트  │    │  기술면접 │    │ 심층면접  │    │  협의    │
│          │    │          │    │          │    │          │    │          │
│ 이력서   │    │ SV/UVM   │    │ UVM 개념 │    │ 설계문제 │    │ 연봉    │
│ 포트폴리오│    │ 온라인   │    │ 코드리뷰 │    │ 팀 핏    │    │ 입사일  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
  (15.5절)        (15.3절)        (15.2절)        (15.6절)
```

**각 단계에서 평가하는 것:**

| 단계 | 평가 항목 | 이 책에서 대비하는 곳 |
|------|-----------|---------------------|
| 서류 전형 | UVM/SV 키워드, 프로젝트 경험 | 15.5 이력서 전략 |
| 코딩 테스트 | SystemVerilog 코딩 능력 | 15.3 코드 리뷰 면접 |
| 1차 기술 면접 | UVM 개념 이해도, 코드 리뷰 | 15.2 빈출 질문 + 15.3 |
| 2차 심층 면접 | 설계 문제 해결, 팀 적합성 | 15.6 면접 시뮬레이션 |
| 처우 협의 | 연봉, 복지, 성장 가능성 | 15.6.3 팔로업 |

### 15.1.3 신입 vs 경력의 기대치 차이

면접에서 신입에게 기대하는 것과 경력에게 기대하는 것은 다릅니다:

| 항목 | 신입 (0~2년) | 경력 (3년+) |
|------|-------------|-------------|
| **UVM 지식** | 기본 컴포넌트 이해, 간단한 TB 구축 | 복잡한 환경 설계, 성능 최적화 |
| **코딩** | 문법 정확성, 기본 패턴 | 효율적 코드, 재사용 가능한 설계 |
| **디버깅** | 에러 메시지 읽기, 기본 파형 분석 | 복잡한 타이밍 이슈, 시스템 레벨 |
| **커뮤니케이션** | 질문할 줄 아는 능력 | 기술 문서 작성, 설계팀 협업 |
| **기대하지 않는 것** | 완벽한 UVM 지식 | — |

> 💡 **안심하세요**: 신입에게는 **"배울 수 있는 기반이 있는가?"**를 봅니다. 이 책을 완독하고 포트폴리오를 만들었다면, 그 기반은 충분합니다.

---

## 15.2 UVM 면접 빈출 질문 Top 30

> **이 절의 목표**: 면접에서 자주 나오는 UVM 질문 30개를 카테고리별로 정리하고, 모범 답안을 연습합니다.

면접 답변의 황금 구조는 **"핵심 → 이유 → 예시"**입니다:

```
답변 구조: "~는 ~입니다. 왜냐하면 ~이기 때문입니다. 예를 들어 ~"
```

면접 질문은 세 가지 카테고리로 나뉩니다:

```
면접 질문 카테고리 맵

┌──────────────────────────────────────────────────────────────┐
│                    UVM 면접 질문 30선                         │
├──────────┬──────────────────────┬────────────────────────────┤
│  기초    │  컴포넌트/아키텍처    │  고급/실무                  │
│ (10문항) │  (10문항)             │  (10문항)                  │
│          │                      │                            │
│ Q1~Q10   │  Q11~Q20             │  Q21~Q30                   │
│          │                      │                            │
│ UVM 정의 │  Agent 구조          │  Constrained Random        │
│ Object   │  Driver/Monitor      │  Coverage Closure          │
│ Factory  │  Scoreboard          │  Reset 처리                │
│ Phase    │  Analysis Port       │  VIP 활용                  │
│ TLM      │  Environment         │  성능 최적화               │
│ Sequence │  RAL                 │  field macro               │
│ Virtual  │  Virtual Sequence    │  end_of_elaboration        │
│  IF      │  Coverage            │  Multi-agent               │
│ config_db│  Assertion           │  에러 주입                 │
│ Objection│  Callback            │  TB 구축 순서              │
│ seq_item │                      │                            │
├──────────┴──────────────────────┴────────────────────────────┤
│ 신입: 기초 필수 + 컴포넌트 대부분 | 경력: 전 카테고리         │
└──────────────────────────────────────────────────────────────┘
```

### 15.2.1 기초 개념 (10문항)

이 카테고리는 **모든 면접에서 반드시** 나옵니다. 정확하게 답하지 못하면 탈락입니다.

**Q1. UVM이란 무엇이며, 왜 사용하는가?**

<details>
<summary>모범 답안 보기</summary>

UVM(Universal Verification Methodology)은 SystemVerilog 기반의 **검증 방법론 라이브러리**입니다. 왜 사용하는가 하면, **재사용 가능한 검증 환경**을 표준화된 방식으로 구축할 수 있기 때문입니다. 예를 들어 UART 검증 환경을 만들면, 다른 프로젝트에서 UART를 사용할 때 동일한 에이전트를 재사용할 수 있습니다.

**키포인트**: 표준화(모든 회사가 같은 방법론), 재사용(VIP), 자동화(랜덤 테스트, 커버리지)

> Ch.1 복습
</details>

**Q2. uvm_object와 uvm_component의 차이는?**

<details>
<summary>모범 답안 보기</summary>

`uvm_object`는 **데이터**를 표현하는 기본 클래스이고, `uvm_component`는 **테스트벤치 구조**를 구성하는 클래스입니다. 가장 큰 차이는 `uvm_component`는 **Phase 메커니즘**과 **계층 구조(parent-child)**를 가진다는 점입니다. 예를 들어 트랜잭션(`uvm_sequence_item`)은 `uvm_object`이고, 드라이버(`uvm_driver`)는 `uvm_component`입니다.

**키포인트**: object=데이터/일시적, component=구조/영구적, component만 Phase 참여

**주의**: Factory 등록 매크로도 다릅니다. object 계열은 `` `uvm_object_utils ``, component 계열은 `` `uvm_component_utils ``를 사용합니다. 이 둘을 혼동하면 컴파일 에러가 발생합니다.

> Ch.4 복습
</details>

**Q3. Factory Pattern이란? 왜 new() 대신 create()를 쓰는가?**

<details>
<summary>모범 답안 보기</summary>

Factory Pattern은 **객체 생성을 중앙에서 관리**하는 디자인 패턴입니다. `new()` 대신 `create()`를 쓰는 이유는 **런타임에 클래스를 교체(override)**할 수 있기 때문입니다. 예를 들어 테스트 A에서는 기본 드라이버를 쓰고, 테스트 B에서는 에러 주입 드라이버로 교체할 때, 환경 코드를 수정하지 않고 Factory override만 하면 됩니다.

> 💡 **비유**: 자동차 공장의 **생산 라인**과 같습니다. 세단을 만들던 라인에서 SUV를 만들고 싶을 때, 공장 전체를 새로 짓지 않고 **라인(클래스)만 교체**하면 됩니다. `create()`가 바로 이 "교체 가능한 생산 라인"입니다. `new()`를 쓰면 "세단 전용 공장"이 되어 SUV를 만들려면 공장을 새로 지어야 합니다.

```systemverilog
// new()를 쓰면 — 교체 불가능 (세단 전용 공장)
uart_driver drv = new("drv", this);

// create()를 쓰면 — Factory가 관리, override 가능 (교체 가능 생산 라인)
uart_driver drv = uart_driver::type_id::create("drv", this);
```

**키포인트**: 재사용성, 유연성, 테스트별 커스터마이징

> Ch.4 복습
</details>

**Q4. UVM Phase란? build_phase와 run_phase의 차이는?**

<details>
<summary>모범 답안 보기</summary>

UVM Phase는 테스트벤치의 **실행 순서를 자동으로 관리**하는 메커니즘입니다. `build_phase`는 **컴포넌트를 생성**하는 단계(top-down)이고, `run_phase`는 **시뮬레이션을 실행**하는 단계입니다. 핵심 차이는 `build_phase`는 `function`(시간 소모 없음)이고, `run_phase`는 `task`(시간 소모 가능, 클록 대기 가능)입니다.

**Phase 순서**: build → connect → end_of_elaboration → start_of_simulation → run → extract → check → report

**키포인트**: build=구조 생성, connect=연결, run=시뮬레이션 실행

> Ch.4 복습
</details>

**Q5. TLM(Transaction Level Modeling)이란?**

<details>
<summary>모범 답안 보기</summary>

TLM은 **신호 레벨이 아닌 트랜잭션 레벨**로 컴포넌트 간 통신하는 방식입니다. 왜 사용하는가 하면, 신호 하나하나 연결하면 복잡하고 재사용이 어렵지만, 트랜잭션 단위로 통신하면 **추상화 수준이 높아져** 코드가 간결하고 재사용 가능해지기 때문입니다.

**핵심 포트 종류**:
- `uvm_blocking_put_port`: 1:1 통신 (드라이버↔시퀀서)
- `uvm_analysis_port`: 1:N 브로드캐스트 (모니터→스코어보드, 커버리지)

**중요한 특성**: `uvm_analysis_port`의 `write()` 메서드는 **non-blocking**입니다. 모니터가 `ap.write(item)`을 호출하면 연결된 모든 구독자(Scoreboard, Coverage Collector 등)의 `write()`가 순차적으로 호출됩니다. 구독자가 0개여도 에러가 발생하지 않습니다 — 이것이 Regular Port와의 핵심 차이입니다.

**키포인트**: 추상화, 재사용, 1:N 브로드캐스트, non-blocking

> Ch.8 복습
</details>

**Q6. Sequence와 Sequencer의 역할 차이는?**

<details>
<summary>모범 답안 보기</summary>

**Sequence**는 **트랜잭션을 생성하는 시나리오**(무엇을 보낼지)이고, **Sequencer**는 Sequence와 Driver 사이에서 **트랜잭션을 중재하는 라우터**(언제, 누구 것을 보낼지)입니다. Sequence가 식당의 "주문서"라면, Sequencer는 "주문을 받아 주방(Driver)에 전달하는 웨이터"입니다.

```systemverilog
// Sequence — 시나리오 정의
class write_seq extends uvm_sequence #(apb_seq_item);
  `uvm_object_utils(write_seq)  // Sequence는 uvm_object_utils!

  virtual task body();
    req = apb_seq_item::type_id::create("req");
    start_item(req);
    req.randomize() with { pwrite == 1; };
    finish_item(req);
  endtask
endclass
```

**키포인트**: Sequence=시나리오, Sequencer=중재, Driver=실행

> Ch.6 복습
</details>

**Q7. Virtual Interface란? 왜 필요한가?**

<details>
<summary>모범 답안 보기</summary>

Virtual Interface는 **클래스 기반 테스트벤치에서 모듈의 인터페이스에 접근**하기 위한 핸들입니다. SystemVerilog에서 클래스(`class`)는 모듈(`module`)의 신호에 직접 접근할 수 없기 때문에 필요합니다. `interface`를 정의하고, 그 핸들을 `virtual interface`로 클래스에 전달하면 DUT 신호를 구동/관찰할 수 있습니다.

**키포인트**: 클래스↔모듈 연결 다리, config_db로 전달, Driver/Monitor에서 사용

> Ch.7, Ch.11 복습
</details>

**Q8. uvm_config_db란? 사용 목적은?**

<details>
<summary>모범 답안 보기</summary>

`uvm_config_db`는 **컴포넌트 간 설정 값을 전달하는 전역 데이터베이스**입니다. 주로 Virtual Interface 전달, Agent 모드 설정(ACTIVE/PASSIVE), 테스트 파라미터 전달에 사용합니다. `set()`으로 값을 저장하고 `get()`으로 가져옵니다.

```systemverilog
// Top에서 set
uvm_config_db#(virtual apb_if)::set(null, "uvm_test_top.env.agent*", "vif", apb_if_inst);

// Driver에서 get
uvm_config_db#(virtual apb_if)::get(this, "", "vif", vif);
```

**키포인트**: 계층 간 설정 전달, 하드코딩 방지, 유연한 구성

> Ch.4, Ch.11 복습
</details>

**Q9. Objection Mechanism이란?**

<details>
<summary>모범 답안 보기</summary>

Objection은 **시뮬레이션 종료를 제어하는 메커니즘**입니다. `raise_objection()`으로 "아직 할 일이 있다"고 선언하고, `drop_objection()`으로 "끝났다"고 알립니다. 모든 Objection이 해제되면 시뮬레이션이 종료됩니다.

```systemverilog
task run_phase(uvm_phase phase);
  phase.raise_objection(this);  // 시작
  // ... 테스트 시나리오 ...
  phase.drop_objection(this);   // 종료
endtask
```

**키포인트**: raise/drop 쌍, 보통 Test 레벨에서만 사용, 누락 시 즉시 종료

> Ch.4 복습
</details>

**Q10. uvm_sequence_item의 역할은?**

<details>
<summary>모범 답안 보기</summary>

`uvm_sequence_item`은 **검증 환경에서 주고받는 데이터의 단위**인 트랜잭션(Transaction)을 정의하는 클래스입니다. DUT의 프로토콜에 맞는 필드(주소, 데이터, 제어 신호 등)를 `rand`로 선언하여 **랜덤 테스트**가 가능하게 합니다. `uvm_object`를 상속하므로 `copy()`, `compare()`, `print()` 등의 유틸리티 기능을 활용할 수 있습니다.

**키포인트**: 트랜잭션 정의, rand 필드, `uvm_field_*` 매크로 또는 do_copy/do_compare 구현

> Ch.6, Ch.11 복습
</details>

### 15.2.2 컴포넌트 & 아키텍처 (10문항)

이 카테고리는 **UVM 테스트벤치 구조를 이해하고 있는지** 확인합니다.

**Q11. UVM Agent의 구조를 설명하라.**

<details>
<summary>모범 답안 보기</summary>

UVM Agent는 **DUT의 하나의 인터페이스를 검증하는 단위**입니다. 세 개의 핵심 컴포넌트로 구성됩니다:
- **Sequencer**: 트랜잭션 흐름 중재
- **Driver**: 트랜잭션을 DUT 신호로 변환
- **Monitor**: DUT 신호를 트랜잭션으로 변환 (관찰)

Agent는 **ACTIVE** 모드(Sequencer+Driver+Monitor)와 **PASSIVE** 모드(Monitor만)로 동작합니다. PASSIVE 모드는 신호를 관찰만 할 때 사용합니다.

**키포인트**: Sequencer-Driver-Monitor 삼총사, ACTIVE/PASSIVE 모드, Agent는 재사용 단위

> Ch.7, Ch.11 복습
</details>

**Q12. Driver와 Monitor의 차이는?**

<details>
<summary>모범 답안 보기</summary>

**Driver**는 트랜잭션을 받아 **DUT 입력 신호를 구동**(drive)하는 역할이고, **Monitor**는 DUT 인터페이스의 신호를 **관찰(observe)하여 트랜잭션으로 변환**하는 역할입니다. 핵심 차이는 Driver는 DUT에 **능동적으로** 신호를 보내고, Monitor는 **수동적으로** 관찰만 합니다.

**키포인트**: Driver=구동(능동), Monitor=관찰(수동), Monitor는 항상 존재(PASSIVE 모드에서도)

> Ch.7 복습
</details>

**Q13. Scoreboard의 역할과 구현 방법은?**

<details>
<summary>모범 답안 보기</summary>

Scoreboard는 **DUT의 출력이 예상 결과와 일치하는지 자동으로 비교**하는 컴포넌트입니다. Monitor의 `analysis_port`에 연결되어 트랜잭션을 수신하고, 내부의 **참조 모델(Reference Model)**과 비교합니다.

구현 방법:
1. `uvm_scoreboard` 상속
2. `uvm_analysis_imp` 또는 `uvm_tlm_analysis_fifo` 사용
3. `write()` 메서드에서 비교 로직 구현

**키포인트**: 자동 비교, analysis port 연결, 참조 모델

> Ch.8 복습
</details>

**Q14. Analysis Port와 Regular Port의 차이는?**

<details>
<summary>모범 답안 보기</summary>

**Regular Port**(`uvm_blocking_put_port` 등)는 **1:1 통신**으로, 데이터를 보내고 받는 양쪽이 연결되어야 합니다. **Analysis Port**(`uvm_analysis_port`)는 **1:N 브로드캐스트**로, 하나의 송신자(보통 Monitor)가 여러 수신자(Scoreboard, Coverage Collector 등)에게 동시에 데이터를 보낼 수 있습니다.

**핵심 차이**: Analysis Port는 연결된 구독자가 0개여도 에러가 나지 않습니다 (non-blocking). `write()` 호출 시 모든 구독자의 `write()`가 순차 호출되지만, 포트 자체에는 blocking이 없습니다.

**키포인트**: Regular=1:1/blocking, Analysis=1:N/non-blocking

> Ch.8 복습
</details>

**Q15. Environment(uvm_env)의 역할은?**

<details>
<summary>모범 답안 보기</summary>

`uvm_env`는 **Agent, Scoreboard, Coverage Collector 등을 하나로 묶는 컨테이너**입니다. 재사용의 핵심 단위로, 하나의 Environment에 여러 Agent와 Scoreboard를 조합하여 복잡한 검증 환경을 구성합니다.

**키포인트**: 컴포넌트 조합 컨테이너, 재사용 단위, Test에서 인스턴스화

> Ch.5, Ch.11 복습
</details>

**Q16. RAL(Register Abstraction Layer)이란?**

<details>
<summary>모범 답안 보기</summary>

RAL은 DUT의 **레지스터를 소프트웨어 객체로 추상화**하여 접근하는 계층입니다. 물리적 주소/데이터 대신 `reg_block.reg_name.field_name.write(value)` 같은 **의미 있는 이름**으로 레지스터를 읽고 쓸 수 있습니다. RAL은 내부적으로 Adapter를 통해 시퀀스 아이템으로 변환합니다.

**키포인트**: 레지스터 추상화, 이름 기반 접근, 미러 기능(예상값 추적), Adapter로 변환

> Ch.12 복습
</details>

**Q17. Virtual Sequence란? 왜 필요한가?**

<details>
<summary>모범 답안 보기</summary>

Virtual Sequence는 **여러 Agent의 Sequencer를 동시에 제어**하는 상위 시퀀스입니다. 예를 들어 APB Agent와 AXI Agent가 있을 때, 두 인터페이스에 대한 시나리오를 하나의 Virtual Sequence에서 조율할 수 있습니다.

```systemverilog
class system_vseq extends uvm_sequence;
  `uvm_object_utils(system_vseq)  // Virtual Sequence도 uvm_object_utils!

  apb_sequencer apb_sqr;
  axi_sequencer axi_sqr;

  virtual task body();
    fork
      apb_write_seq.start(apb_sqr);  // APB 쓰기
      axi_read_seq.start(axi_sqr);   // AXI 읽기 (동시)
    join
  endtask
endclass
```

**키포인트**: 다중 Agent 조율, Virtual Sequencer에서 핸들 관리, fork-join으로 동시 실행

> Ch.13 복습
</details>

**Q18. Coverage란? Functional Coverage와 Code Coverage의 차이는?**

<details>
<summary>모범 답안 보기</summary>

Coverage는 **검증이 얼마나 충분한지 측정하는 지표**입니다.
- **Code Coverage**: 시뮬레이터가 자동 수집. RTL 코드의 몇 %가 실행되었는지 (line, branch, toggle, FSM 등)
- **Functional Coverage**: 검증 엔지니어가 직접 정의. **원하는 시나리오가 실행되었는지** (주소 범위, 읽기/쓰기 조합, 연속 패턴 등)

**키포인트**: Code=자동/RTL 기준, Functional=수동/스펙 기준, 둘 다 필요

> Ch.14 복습
</details>

**Q19. Assertion이란? Immediate vs Concurrent의 차이는?**

<details>
<summary>모범 답안 보기</summary>

Assertion은 **"이 조건이 항상 참이어야 한다"**를 선언하는 검증 기법입니다.
- **Immediate Assertion**: 절차적 코드 안에서 **즉시** 평가 (combinational)
- **Concurrent Assertion**: **클록 기반**으로 시간에 걸쳐 평가 (sequential)

```systemverilog
// Immediate — 지금 이 순간 체크
assert (paddr < 16) else $error("주소 범위 초과!");

// Concurrent — 클록 기반 시퀀스 체크
assert property (@(posedge clk) psel |-> ##1 penable);
```

**키포인트**: Immediate=즉시/combinational, Concurrent=클록/temporal, SVA는 Concurrent

> Ch.14 복습
</details>

**Q20. Callback이란? 언제 사용하는가?**

<details>
<summary>모범 답안 보기</summary>

Callback은 **기존 코드를 수정하지 않고 동작을 추가/변경**할 수 있는 메커니즘입니다. Driver나 Monitor에 미리 정의된 훅(hook) 포인트에 새로운 동작을 등록합니다. 예를 들어 Driver의 트랜잭션 전송 전/후에 에러를 주입하거나 로그를 추가할 때 사용합니다.

**키포인트**: 코드 수정 없이 동작 추가, 에러 주입/로깅, VIP 커스터마이징

> Ch.13 복습
</details>

### 15.2.3 고급 주제 & 실무 (10문항)

이 카테고리는 **실무 경험과 깊은 이해**를 확인합니다. 경력 면접에서 더 비중이 높습니다.

**Q21. Constrained Random Verification이란?**

<details>
<summary>모범 답안 보기</summary>

Constrained Random Verification은 **제약 조건 내에서 랜덤으로 테스트 시나리오를 생성**하는 검증 방법입니다. 완전히 랜덤이면 무효한 시나리오가 생기고, 완전히 지정하면 커버리지가 부족합니다. constraint로 유효 범위를 제한하면서 그 안에서 다양한 조합을 자동 생성합니다.

```systemverilog
class apb_seq_item extends uvm_sequence_item;
  rand bit [3:0]  paddr;
  rand bit [31:0] pwdata;
  rand bit        pwrite;

  constraint valid_addr { paddr inside {[0:15]}; }
  constraint write_bias { pwrite dist {1 := 70, 0 := 30}; }  // 쓰기 70%
endclass
```

**키포인트**: 유효 범위 내 자동 다양화, constraint, dist로 비중 조절

> Ch.9 복습
</details>

**Q22. Coverage Closure란? 어떻게 달성하는가?**

<details>
<summary>모범 답안 보기</summary>

Coverage Closure는 **목표 커버리지에 도달하기 위한 반복적 프로세스**입니다:
1. 랜덤 테스트 실행 → 커버리지 리포트 분석
2. 미달 항목(hole) 식별
3. 타겟 시퀀스 작성 (hole을 채우는 특정 시나리오)
4. 재실행 → 리포트 확인 → 반복

실무에서는 보통 랜덤 테스트로 80%, 타겟 테스트로 나머지 20%를 달성합니다.

**키포인트**: 반복적 프로세스, 랜덤+타겟 조합, 100% 달성이 목표가 아닐 수도 있음 (waiver)

> Ch.14 복습
</details>

**Q23. UVM에서 Reset 처리는 어떻게 하는가?**

<details>
<summary>모범 답안 보기</summary>

Reset 처리는 검증에서 중요한 시나리오입니다. UVM에서는 보통:
1. **Sequence에서 reset 시퀀스** 작성 (reset 신호 구동)
2. **Monitor에서 reset 감지** 후 내부 상태 초기화
3. **Scoreboard에서 reset 시 예상 값 초기화**
4. **Driver에서 reset 중 트랜잭션 처리 중단**

```systemverilog
// Monitor에서 reset 감지 예시
forever begin
  @(negedge vif.rst_n);
  // reset 시작 — 진행 중인 트랜잭션 무효화
  @(posedge vif.rst_n);
  // reset 해제 — 모니터링 재개
end
```

실무에서는 **`uvm_heartbeat`**를 함께 사용하여 reset 후 hang(무응답)을 감지합니다. Heartbeat는 특정 Objection이 주기적으로 갱신되는지 모니터링하여, 갱신이 없으면 "시뮬레이션이 멈췄다"고 경고합니다.

**키포인트**: 모든 컴포넌트가 reset에 반응해야 함, Sequence에서 reset 시나리오 작성, heartbeat로 hang 감지

> Ch.7 복습
</details>

**Q24. VIP(Verification IP)란? 어떻게 사용하는가?**

<details>
<summary>모범 답안 보기</summary>

VIP는 **특정 프로토콜(APB, AXI, PCIe 등)에 대한 사전 검증된 UVM 에이전트**입니다. 직접 만들지 않고 Synopsys, Cadence, Siemens 등에서 제공하는 상용 VIP를 사용합니다. VIP에는 Agent, Sequence Library, Coverage Model, Protocol Checker가 포함됩니다.

**사용 시 핵심**:
- VIP의 시퀀스 라이브러리를 활용하여 테스트 작성
- Factory override로 커스터마이징
- Callback으로 추가 동작 삽입

**키포인트**: 상용 검증 IP, 재사용, 프로토콜 표준 준수 보장

> Ch.12 복습
</details>

**Q25. 시뮬레이션 성능을 개선하는 방법은?**

<details>
<summary>모범 답안 보기</summary>

UVM 시뮬레이션 성능 개선 주요 방법:
1. **verbosity 줄이기**: `UVM_HIGH`→`UVM_LOW`로 로그 출력 최소화
2. **$display 제거**: 대신 `uvm_info` 사용 (verbosity 제어 가능)
3. **불필요한 field macro 제거**: `uvm_field_*` 매크로는 느림, do_copy/do_compare 직접 구현
4. **커버리지 선택적 수집**: 불필요한 covergroup disable
5. **병렬 시뮬레이션**: 테스트를 여러 시드로 병렬 실행

**키포인트**: field macro 오버헤드, verbosity 제어, 병렬 리그레션

> Ch.10 복습
</details>

**Q26. `uvm_field_*` 매크로의 장단점은?**

<details>
<summary>모범 답안 보기</summary>

**장점**: `copy()`, `compare()`, `print()`, `pack()/unpack()` 등을 자동 생성하여 코드가 간결합니다.

**단점**: 내부적으로 문자열 기반 처리를 하므로 **성능이 느립니다**. 대규모 시뮬레이션에서는 `do_copy()`, `do_compare()`, `do_print()` 등을 직접 구현하는 것이 권장됩니다.

```systemverilog
// field macro (간편하지만 느림)
`uvm_field_int(paddr, UVM_ALL_ON)

// do_compare (수동이지만 빠름)
function bit do_compare(uvm_object rhs, uvm_comparer comparer);
  apb_seq_item rhs_;
  $cast(rhs_, rhs);
  return (paddr == rhs_.paddr) && (pwdata == rhs_.pwdata);
endfunction
```

**키포인트**: 소규모=macro 편리, 대규모=do_* 직접 구현, 성능 차이 유의

> Ch.4 복습
</details>

**Q27. end_of_elaboration_phase의 용도는?**

<details>
<summary>모범 답안 보기</summary>

`end_of_elaboration_phase`는 **모든 컴포넌트가 build/connect를 완료한 후** 실행되는 Phase입니다. 주로 다음 용도로 사용합니다:
- UVM 토폴로지 출력 (`uvm_top.print_topology()`)
- 최종 설정 확인
- 컴포넌트 간 교차 참조 설정

**키포인트**: build/connect 완료 후 실행, 디버깅/확인 용도, function phase

> Ch.4 복습
</details>

**Q28. Multi-agent 환경 설계 시 고려사항은?**

<details>
<summary>모범 답안 보기</summary>

여러 Agent가 있는 환경에서 고려할 사항:
1. **Virtual Sequencer**: 여러 Agent의 Sequencer 핸들을 모아 조율
2. **Scoreboard 연결**: 여러 Monitor의 트랜잭션을 하나의 Scoreboard에서 비교
3. **동기화**: `fork-join`으로 동시 시나리오, 이벤트(`uvm_event`)로 Agent 간 동기화
4. **Clock domain**: Agent별 다른 클록 도메인 처리

**키포인트**: Virtual Sequencer로 조율, Analysis Port로 Scoreboard 연결, 동기화

> Ch.13 복습
</details>

**Q29. UVM에서 에러 주입(Error Injection)은 어떻게 하는가?**

<details>
<summary>모범 답안 보기</summary>

에러 주입 방법:
1. **Sequence에서 잘못된 트랜잭션 생성**: constraint를 조작하여 프로토콜 위반 시나리오
2. **Callback을 통한 Driver 수정**: 전송 직전에 데이터 변조
3. **Factory Override**: 기본 트랜잭션을 에러 트랜잭션으로 교체

```systemverilog
// Sequence에서 에러 주입 예시
class error_seq extends uvm_sequence #(apb_seq_item);
  `uvm_object_utils(error_seq)  // Sequence → uvm_object_utils

  virtual task body();
    req = apb_seq_item::type_id::create("req");
    start_item(req);
    // 의도적으로 유효 범위 밖 주소 사용
    req.randomize() with { paddr > 4'hF; };
    finish_item(req);
  endtask
endclass
```

**키포인트**: Sequence 조작, Callback, Factory Override

> Ch.9, Ch.13 복습
</details>

**Q30. 실무에서 UVM 테스트벤치를 처음부터 구축하는 순서는?**

<details>
<summary>모범 답안 보기</summary>

실무에서의 구축 순서:
1. **스펙 분석**: DUT 인터페이스, 프로토콜 이해
2. **Transaction 정의**: `uvm_sequence_item` 필드 설계
3. **Interface 정의**: DUT 연결용 `interface` 작성
4. **Agent 구축**: Driver → Monitor → Sequencer → Agent 순
5. **Environment 구성**: Agent + Scoreboard + Coverage Collector
6. **기본 테스트 작성**: Smoke test (간단한 읽기/쓰기)
7. **커버리지 모델 추가**: Functional Coverage 정의
8. **어서션 추가**: 프로토콜 규칙 SVA
9. **테스트 시나리오 확장**: Random + Directed 테스트
10. **커버리지 클로저**: 목표 달성까지 반복

**키포인트**: 스펙→Transaction→Agent→Env→Test→Coverage→Closure 순서

> Ch.1~14 전체 복습
</details>

---

## 15.3 코드 리뷰 면접 대비

> **이 절의 목표**: UVM 코드에서 버그를 찾고 개선안을 제시하는 능력을 연습합니다.

코드 리뷰 면접에서 **자주 혼동하는 매크로 구분**을 먼저 정리합시다:

| 클래스 종류 | Factory 등록 매크로 | 예시 |
|------------|-------------------|------|
| uvm_component 계열 | `` `uvm_component_utils `` | Driver, Monitor, Agent, Env, Test |
| uvm_object 계열 | `` `uvm_object_utils `` | Sequence, Transaction(seq_item) |

> 이 구분을 혼동하면 **컴파일 에러**가 발생합니다. 면접에서 가장 흔히 테스트하는 포인트 중 하나입니다.

### 15.3.1 "이 코드의 문제를 찾아라" 유형

**면접관이 UVM 코드를 보여주고 "무엇이 잘못되었는가?" 물어봅니다.** 이 유형은 UVM을 실제로 사용해본 사람과 아닌 사람을 구분합니다.

**문제 1: 쉬움 — Driver에서의 3가지 문제**

```systemverilog
// apb_driver.sv — 이 코드에서 문제 3가지를 찾아라

class apb_driver extends uvm_driver;  // (1)
  virtual apb_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    // (2) super.build_phase 생략
    uvm_config_db#(virtual apb_if)::get(this, "", "vif", vif);
  endfunction

  virtual task run_phase(uvm_phase phase);
    forever begin
      seq_item_port.get_next_item(req);
      vif.paddr  = req.paddr;
      vif.pwdata = req.pwdata;
      vif.pwrite = req.pwrite;
      vif.psel   = 1;
      // (3) penable 타이밍 누락
      @(posedge vif.clk);
      vif.psel   = 0;
      seq_item_port.item_done();
    end
  endtask
endclass
```

<details>
<summary>정답 보기</summary>

**문제 1**: 파라미터화 누락
```systemverilog
// 잘못됨
class apb_driver extends uvm_driver;
// 올바름
class apb_driver extends uvm_driver #(apb_seq_item);
```
`uvm_driver`는 `#(REQ)`로 트랜잭션 타입을 파라미터로 받아야 합니다. 누락하면 `req`의 타입이 `uvm_sequence_item`이 되어 필드 접근 시 `$cast`가 필요합니다.

**문제 2**: `super.build_phase(phase)` 누락
```systemverilog
function void build_phase(uvm_phase phase);
  super.build_phase(phase);  // 반드시 호출!
  // ...
endfunction
```
부모 클래스의 build 로직이 실행되지 않아 예기치 않은 동작이 발생할 수 있습니다.

**문제 3**: APB 프로토콜 위반 — `penable` 처리 누락
```systemverilog
// 올바른 APB 프로토콜:
// Setup phase: psel=1, penable=0 (1사이클)
// Access phase: psel=1, penable=1 (pready까지)
vif.psel    = 1;
vif.penable = 0;
@(posedge vif.clk);     // Setup phase
vif.penable = 1;
@(posedge vif.clk iff vif.pready);  // Access phase (pready 대기)
vif.psel    = 0;
vif.penable = 0;
```

**추가 문제**: `` `uvm_component_utils `` 매크로도 누락되었습니다 — Factory에 등록되지 않아 `create()` 사용 불가.
</details>

**문제 2: 보통 — Scoreboard의 문제**

```systemverilog
// apb_scoreboard.sv — 이 코드의 문제를 찾아라

class apb_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(apb_scoreboard)

  uvm_analysis_imp #(apb_seq_item, apb_scoreboard) analysis_export;

  bit [31:0] memory [bit[3:0]];  // 참조 모델

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    analysis_export = new("analysis_export", this);
  endfunction

  function void write(apb_seq_item item);
    if (item.pwrite) begin
      memory[item.paddr] = item.pwdata;
    end else begin
      if (memory[item.paddr] != item.prdata) begin
        `uvm_error(get_type_name(),
          $sformatf("Mismatch! addr=0x%0h exp=0x%0h got=0x%0h",
            item.paddr, memory[item.paddr], item.prdata))
      end
    end
  endfunction
endclass
```

<details>
<summary>정답 보기</summary>

**문제 1**: 읽기 검증에서 **초기화되지 않은 메모리 접근** 위험
```systemverilog
// 쓰기 전에 읽기가 먼저 오면?
// memory[addr]가 존재하지 않으므로 0과 비교 — 잘못된 결과
function void write(apb_seq_item item);
  if (item.pwrite) begin
    memory[item.paddr] = item.pwdata;
  end else begin
    if (!memory.exists(item.paddr)) begin
      `uvm_warning(get_type_name(),
        $sformatf("Read from uninitialized addr 0x%0h", item.paddr))
    end else if (memory[item.paddr] != item.prdata) begin
      // 비교 ...
    end
  end
endfunction
```

**문제 2**: 읽기와 쓰기를 **같은 analysis port**로 받는데, **순서 보장 문제**가 있을 수 있음. 쓰기 트랜잭션이 DUT에서 처리되기 전에 같은 주소의 읽기가 올 수 있습니다. 실무에서는 **FIFO 기반** 비교나 **타이밍 고려**가 필요합니다.

**문제 3**: 에러 카운트 관리 없음 — 몇 개의 비교를 했고 몇 개가 실패했는지 `report_phase`에서 요약하는 것이 좋습니다.
</details>

**문제 3: 어려움 — Environment 구조 문제**

```systemverilog
// apb_env.sv — 이 환경의 설계 문제를 찾아라

class apb_env extends uvm_env;
  `uvm_component_utils(apb_env)

  apb_driver    driver;
  apb_monitor   monitor;
  apb_sequencer sequencer;
  apb_scoreboard scoreboard;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    driver     = apb_driver::type_id::create("driver", this);
    monitor    = apb_monitor::type_id::create("monitor", this);
    sequencer  = apb_sequencer::type_id::create("sequencer", this);
    scoreboard = apb_scoreboard::type_id::create("scoreboard", this);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    driver.seq_item_port.connect(sequencer.seq_item_export);
    monitor.ap.connect(scoreboard.analysis_export);
  endfunction
endclass
```

<details>
<summary>정답 보기</summary>

**핵심 문제: Agent 계층이 없음**

Driver, Monitor, Sequencer가 Environment에 직접 있으면 **재사용이 불가능**합니다. 이것들은 **Agent** 안에 캡슐화되어야 합니다:

```systemverilog
// 올바른 구조
class apb_env extends uvm_env;
  `uvm_component_utils(apb_env)

  apb_agent      agent;       // Agent가 Driver/Monitor/Sequencer를 포함
  apb_scoreboard scoreboard;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    agent      = apb_agent::type_id::create("agent", this);
    scoreboard = apb_scoreboard::type_id::create("scoreboard", this);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    agent.monitor.ap.connect(scoreboard.analysis_export);
  endfunction
endclass
```

**왜 Agent가 필요한가?**
- **ACTIVE/PASSIVE 모드**: Agent 없이는 모드 전환 불가
- **재사용**: Agent 단위로 다른 Environment에 통합
- **캡슐화**: Driver-Sequencer 연결은 Agent 내부 문제

이것은 **면접에서 아키텍처 이해도를 측정하는 핵심 질문**입니다.
</details>

### 15.3.2 "이 환경을 개선해라" 유형

이 유형은 동작하는 코드를 **더 좋게 만드는 능력**을 봅니다.

**문제: 다음 테스트를 개선하라**

```systemverilog
class basic_test extends uvm_test;
  `uvm_component_utils(basic_test)
  apb_env env;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = apb_env::type_id::create("env", this);
  endfunction

  virtual task run_phase(uvm_phase phase);
    apb_seq_item req;
    phase.raise_objection(this);

    // 100번 랜덤 쓰기
    repeat(100) begin
      req = apb_seq_item::type_id::create("req");
      start_item(req);
      req.randomize() with { pwrite == 1; };
      finish_item(req);
    end

    // 100번 랜덤 읽기
    repeat(100) begin
      req = apb_seq_item::type_id::create("req");
      start_item(req);
      req.randomize() with { pwrite == 0; };
      finish_item(req);
    end

    phase.drop_objection(this);
  endtask
endclass
```

<details>
<summary>개선안 보기</summary>

**문제점 4가지:**

1. **Test에서 직접 Sequence를 실행하지 않음**: Test는 Sequence를 시작해야지, 직접 `start_item/finish_item`을 하면 안 됩니다.
2. **시퀀스 재사용 불가**: 쓰기 100번, 읽기 100번이 하드코딩되어 있습니다.
3. **쓰기 후 읽기만 테스트**: 읽기→쓰기, 교차 패턴 등 다양한 시나리오가 없습니다.
4. **커버리지 연결 없음**: 테스트 결과를 측정할 수 없습니다.

**개선된 코드:**

```systemverilog
// 1. 재사용 가능한 Sequence 분리
class apb_write_seq extends uvm_sequence #(apb_seq_item);
  `uvm_object_utils(apb_write_seq)  // Sequence는 uvm_object_utils!
  rand int count = 100;

  virtual task body();
    repeat(count) begin
      req = apb_seq_item::type_id::create("req");
      start_item(req);
      req.randomize() with { pwrite == 1; };
      finish_item(req);
    end
  endtask
endclass

// 2. 테스트는 Sequence만 시작
class improved_test extends uvm_test;
  `uvm_component_utils(improved_test)  // Test는 uvm_component_utils!
  apb_env env;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = apb_env::type_id::create("env", this);
  endfunction

  virtual task run_phase(uvm_phase phase);
    apb_write_seq   wr_seq = apb_write_seq::type_id::create("wr_seq");
    apb_read_seq    rd_seq = apb_read_seq::type_id::create("rd_seq");
    apb_mixed_seq   mx_seq = apb_mixed_seq::type_id::create("mx_seq");

    phase.raise_objection(this);
    wr_seq.start(env.agent.sequencer);  // 쓰기
    rd_seq.start(env.agent.sequencer);  // 읽기
    mx_seq.start(env.agent.sequencer);  // 혼합
    phase.drop_objection(this);
  endtask
endclass
```

**핵심**: Test는 **시나리오 조합**만 담당, 세부 구현은 Sequence에 위임.
</details>

### 15.3.3 라이브 코딩 팁

면접에서 화이트보드나 화면 공유로 코드를 작성할 때:

| 팁 | 설명 |
|-----|------|
| **뼈대 먼저** | 클래스 선언, 생성자, Phase 메서드 틀을 먼저 작성 |
| **주석으로 설명** | 코드 전에 "여기서 ~를 할 겁니다" 주석을 먼저 작성 |
| **매크로 잊지 않기** | component는 `` `uvm_component_utils ``, object는 `` `uvm_object_utils `` |
| **super 호출** | `build_phase`, `connect_phase`에서 `super` 호출 습관 |
| **이름 규칙** | `uart_driver`, `apb_monitor` 같은 명확한 네이밍 |
| **완벽하지 않아도 됨** | 전체 로직 흐름을 보여주는 것이 중요 |

```systemverilog
// 라이브 코딩 작성 순서 예시
// Step 1: 클래스 뼈대
class my_driver extends uvm_driver #(my_item);
  `uvm_component_utils(my_driver)
  virtual my_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  // Step 2: build_phase — config_db에서 vif 가져오기
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual my_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "vif를 가져올 수 없습니다")
  endfunction

  // Step 3: run_phase — 핵심 드라이빙 로직
  virtual task run_phase(uvm_phase phase);
    forever begin
      seq_item_port.get_next_item(req);
      // 여기서 프로토콜에 맞게 신호를 구동합니다
      @(posedge vif.clk);
      vif.data <= req.data;
      seq_item_port.item_done();
    end
  endtask
endclass
```

---

## 15.4 포트폴리오 프로젝트 구성

> **이 절의 목표**: Ch.11~14에서 만든 APB 검증 환경을 GitHub 포트폴리오로 정리하여 취업에 활용합니다.

### 15.4.1 Ch.11~14 APB 프로젝트를 포트폴리오로

이 책을 통해 만든 APB 검증 환경은 **이미 포트폴리오가 될 수 있는 수준**입니다. 포함된 기술:

| 챕터 | 기술 | 포트폴리오에서 어필 포인트 |
|------|------|--------------------------|
| Ch.11 | APB Agent (Driver/Monitor/Sequencer) | "UVM Agent를 처음부터 구축한 경험" |
| Ch.12 | RAL (Register Abstraction Layer) | "레지스터 모델을 직접 작성한 경험" |
| Ch.13 | Virtual Sequence | "다중 Agent 환경을 설계한 경험" |
| Ch.14 | Coverage + Assertion | "커버리지 기반 검증 방법론 경험" |

> 💡 **비유**: 이력서가 **"설계도"**(내가 무엇을 할 수 있는지 설명)라면, 포트폴리오는 **"완성된 건물"**(실제로 해봤다는 증거)입니다. 면접관은 설계도보다 건물을 보고 싶어합니다.

### 15.4.2 GitHub 저장소 구조와 README

**권장 저장소 구조:**

```
포트폴리오 GitHub 저장소 구조

apb-uvm-verification/
├── README.md                    ← 프로젝트 소개 (가장 중요!)
├── docs/
│   ├── verification_plan.md     ← 검증 계획서
│   ├── coverage_report.md       ← 커버리지 결과 요약
│   └── architecture.md          ← 아키텍처 설명
├── rtl/
│   └── apb_slave_memory.sv      ← DUT
├── tb/
│   ├── apb_if.sv                ← Interface
│   ├── apb_seq_item.sv          ← Transaction
│   ├── apb_driver.sv            ← Driver
│   ├── apb_monitor.sv           ← Monitor
│   ├── apb_sequencer.sv         ← Sequencer
│   ├── apb_agent.sv             ← Agent
│   ├── apb_scoreboard.sv        ← Scoreboard
│   ├── apb_coverage.sv          ← Coverage Collector
│   ├── apb_assertions.sv        ← Protocol Assertions
│   ├── apb_env.sv               ← Environment
│   ├── apb_reg_model.sv         ← RAL Model
│   ├── apb_virtual_seq.sv       ← Virtual Sequences
│   └── apb_base_test.sv         ← Base Test
├── tests/
│   ├── apb_smoke_test.sv        ← 기본 테스트
│   ├── apb_random_test.sv       ← 랜덤 테스트
│   ├── apb_coverage_test.sv     ← 커버리지 테스트
│   └── apb_error_test.sv        ← 에러 주입 테스트
├── sim/
│   ├── Makefile                 ← 빌드 스크립트
│   └── run.do                   ← 시뮬레이터 스크립트
└── LICENSE
```

**GitHub에 올리는 방법 (step by step):**

```bash
# 1. 저장소 초기화
mkdir apb-uvm-verification
cd apb-uvm-verification
git init

# 2. 파일 구조 생성
mkdir -p docs rtl tb tests sim

# 3. 코드 파일 복사 (Ch.11~14에서 작성한 파일들)
cp /path/to/apb_slave_memory.sv rtl/
cp /path/to/apb_*.sv tb/
cp /path/to/tests/*.sv tests/

# 4. README.md 작성 (아래 템플릿 참고)

# 5. 첫 커밋
git add .
git commit -m "Initial commit: APB UVM verification environment"

# 6. GitHub 저장소 생성 후 연결
git remote add origin https://github.com/your-username/apb-uvm-verification.git
git branch -M main
git push -u origin main
```

**README.md 템플릿:**

````markdown
# APB Slave Memory UVM Verification Environment

## Overview
AMBA APB 프로토콜 기반 Slave Memory의 UVM 검증 환경입니다.
UVM 1.2 표준을 준수하며, Agent/RAL/Coverage/Assertion을 포함합니다.

## Architecture
```
UVM Test
└── Environment
    ├── APB Agent (Active)
    │   ├── Sequencer
    │   ├── Driver
    │   └── Monitor
    ├── RAL Model
    │   └── Adapter
    ├── Scoreboard
    ├── Coverage Collector
    └── Virtual Sequencer
```

## Features
- **APB Agent**: AMBA 3.0 APB 프로토콜 완전 지원
- **RAL Model**: 16개 레지스터 추상화, 미러 검증
- **Coverage**: 주소/데이터/동작 교차 커버리지 (목표: 95%)
- **Assertions**: APB 프로토콜 규칙 5개 SVA 구현
- **Test Suite**: Smoke, Random, Directed, Error Injection

## Results
| 항목 | 결과 |
|------|------|
| 테스트 수 | 15개 |
| Pass Rate | 100% |
| Functional Coverage | 96.1% |
| Assertion Failures | 0 |

## How to Run
```bash
# Questa
cd sim && make questa

# VCS
cd sim && make vcs
```

## Skills Demonstrated
- UVM 1.2 Methodology
- SystemVerilog OOP & Constrained Random
- AMBA APB Protocol
- Coverage-Driven Verification
- SVA (SystemVerilog Assertions)
- Register Abstraction Layer (RAL)
````

### 15.4.3 문서화와 시연 가이드

포트폴리오에서 **차별화 포인트**가 되는 문서들:

**1. 검증 계획서 (Verification Plan)**

```markdown
## 검증 계획서 — APB Slave Memory

### 1. DUT 기능 목록
| 기능     | 설명                 | 검증 방법         |
|----------|----------------------|-------------------|
| 쓰기     | 주소에 데이터 저장   | Directed + Random |
| 읽기     | 주소에서 데이터 반환 | Back-to-back R/W  |
| 프로토콜 | APB 타이밍 준수      | SVA Assertion     |

### 2. 커버리지 목표
| 항목          | 목표 | 현재  |
|---------------|------|-------|
| 주소 커버리지 | 100% | 100%  |
| 동작 커버리지 | 100% | 100%  |
| 교차 커버리지 | 90%  | 96.1% |
```

**2. 커버리지 결과 요약 — 숫자로 증명**

면접관이 가장 보고 싶어하는 것은 **결과 숫자**입니다:
- "커버리지 96.1% 달성"
- "15개 테스트 전수 통과"
- "랜덤 테스트로 80%, 타겟으로 16.1% 추가"

---

## 15.5 이력서 & 자기소개서 전략

> **이 절의 목표**: 검증 엔지니어 이력서를 작성하고, 자기소개서에서 UVM 경험을 효과적으로 어필합니다.

### 15.5.1 검증 엔지니어 이력서 작성법

**이력서의 핵심은 "키워드 매칭"**입니다. 채용 담당자는 이력서에서 관련 키워드를 검색합니다.

**필수 키워드 목록:**

| 카테고리 | 키워드 |
|---------|--------|
| **방법론** | UVM, SystemVerilog, Constrained Random, Coverage-Driven |
| **컴포넌트** | Agent, Driver, Monitor, Sequencer, Scoreboard, Coverage |
| **프로토콜** | APB, AXI, AHB (경험한 것) |
| **기법** | Factory Pattern, RAL, Virtual Sequence, SVA |
| **도구** | VCS, Questa, Xcelium, Verdi, DVE, SimVision |
| **프로세스** | Coverage Closure, Regression, Bug Tracking |
| **버전 관리** | Git, SVN, GitHub |
| **운영체제** | Linux, Shell Script (Bash/Tcl), Makefile |

> 💡 **팁**: Git과 Linux는 이력서에 명시하지 않아도 당연히 사용할 수 있어야 하는 기본 기술입니다. 하지만 신입 이력서에는 명시적으로 포함하는 것이 좋습니다 — 면접관이 "기본기가 있구나"를 확인합니다.

**프로젝트 경험 작성 예시:**

```
나쁜 예:
"UVM으로 테스트벤치를 만들었습니다."

좋은 예:
"APB Slave Memory에 대한 UVM 검증 환경을 구축하였습니다.
- UVM 1.2 기반 Agent(Driver/Monitor/Sequencer) 설계 및 구현
- RAL을 활용한 레지스터 검증 자동화
- Functional Coverage 96.1% 달성 (Constrained Random + Directed 조합)
- SVA 기반 APB 프로토콜 어서션 5개 구현
- 15개 테스트케이스 100% 통과"
```

> 💡 **핵심**: **구체적 숫자**와 **기술 용어**를 사용하세요. "검증을 했다"가 아니라 "Coverage 96.1%를 달성했다"입니다.

### 15.5.2 기술 키워드와 성과 표현

이력서에서 **동사 선택**이 중요합니다:

| 강한 동사 | 예시 |
|-----------|------|
| **설계** | "UVM 검증 환경을 설계하였습니다" |
| **구현** | "APB Agent를 구현하였습니다" |
| **달성** | "Functional Coverage 96%를 달성하였습니다" |
| **자동화** | "커버리지 수집을 자동화하였습니다" |
| **분석** | "커버리지 홀을 분석하여 타겟 시퀀스를 작성하였습니다" |

**성과 표현 공식: 동사 + 대상 + 수치/결과**

```
"RAL을 활용한 레지스터 검증을 자동화하여 검증 효율을 향상시켰습니다"
"5개의 APB 프로토콜 어서션으로 타이밍 위반을 자동 검출하였습니다"
"Constrained Random과 Directed 테스트 조합으로 Coverage Closure를 달성하였습니다"
```

### 15.5.3 자기소개서에서 UVM 경험 어필

자기소개서에서 UVM 프로젝트를 설명하는 **STAR 기법**:

| 단계 | 내용 | 예시 |
|------|------|------|
| **S**(Situation) | 상황 | "APB Slave Memory를 검증해야 하는 상황에서" |
| **T**(Task) | 과제 | "UVM 기반 자동화 검증 환경을 구축하는 것이 목표였습니다" |
| **A**(Action) | 행동 | "Agent, RAL, Coverage Collector, Assertion을 설계하고 구현했습니다" |
| **R**(Result) | 결과 | "Coverage 96.1% 달성, 15개 테스트 100% 통과" |

---

## 15.6 실전 면접 시뮬레이션

> **이 절의 목표**: 실제 면접과 유사한 대화를 통해 답변 연습을 합니다.

### 15.6.1 1차 기술 면접 시뮬레이션

> 상황: 팹리스 반도체 회사의 검증팀 신입 채용 1차 기술 면접

**면접관**: 자기소개와 함께 UVM 프로젝트 경험을 간단히 말씀해주세요.

**지원자 모범 답변**:
> "안녕하세요, 전자공학과를 졸업한 [이름]입니다. 졸업 프로젝트로 APB Slave Memory에 대한 UVM 검증 환경을 구축했습니다. Agent, RAL, Coverage Collector, Assertion을 포함한 완전한 환경을 설계했고, Functional Coverage 96%를 달성했습니다."

---

**면접관**: UVM에서 Factory Pattern이 왜 중요한지 설명해주세요.

**지원자 모범 답변**:
> "Factory Pattern은 테스트별로 컴포넌트나 트랜잭션을 교체할 수 있게 해줍니다. 예를 들어 기본 테스트에서는 일반 드라이버를 쓰고, 에러 주입 테스트에서는 에러 드라이버로 교체할 때, 환경 코드를 전혀 수정하지 않고 Factory override 한 줄로 가능합니다. 이것이 UVM의 재사용성을 가능하게 하는 핵심 메커니즘입니다."

---

**면접관**: Analysis Port와 일반 TLM Port의 차이를 설명해주세요.

**지원자 모범 답변**:
> "일반 TLM Port는 1:1 통신이고 blocking이 가능합니다. 반면 Analysis Port는 1:N 브로드캐스트입니다. Monitor가 트랜잭션을 캡처하면 Scoreboard, Coverage Collector 등 여러 구독자에게 동시에 전달됩니다. 연결된 구독자가 없어도 에러가 나지 않는 점도 차이입니다. write() 호출 시 모든 구독자의 write()가 순차적으로 호출되지만 포트 레벨에서는 non-blocking입니다."

---

**면접관**: 이 코드에서 문제를 찾아보세요. (화면에 코드 표시)

```systemverilog
class my_test extends uvm_test;
  my_env env;
  virtual task run_phase(uvm_phase phase);
    my_seq seq = new("seq");
    seq.start(env.agent.sequencer);
  endtask
endclass
```

**지원자 모범 답변**:
> "세 가지 문제가 있습니다. 첫째, `phase.raise_objection(this)`가 없어서 시뮬레이션이 즉시 종료됩니다. 둘째, Sequence를 `new()`로 생성했는데, Factory를 통해 `create()`로 생성해야 나중에 override가 가능합니다. 셋째, `` `uvm_component_utils`` 매크로가 없어서 이 Test 클래스 자체도 Factory에 등록되지 않습니다."

---

**면접관**: Coverage Closure는 어떻게 진행하나요?

**지원자 모범 답변**:
> "먼저 Constrained Random 테스트를 대량 실행하여 기본 커버리지를 채웁니다. 보통 80% 정도까지 올라갑니다. 그 다음 커버리지 리포트를 분석하여 미달 항목을 찾고, 그 항목을 타겟하는 Directed 시퀀스를 작성합니다. 이 과정을 반복하여 목표 커버리지에 도달합니다. 실제 프로젝트에서 100% 달성이 어려운 경우에는 waiver 문서를 작성하여 달성 불가 사유를 기록합니다."

### 15.6.2 2차 심층 면접 시뮬레이션

> 상황: 2차 면접은 팀 리드나 시니어 엔지니어가 진행. 더 깊은 기술 + 문제 해결 능력 평가

**면접관**: 새로운 SPI IP의 검증 환경을 처음부터 구축한다면, 어떤 순서로 진행하시겠습니까?

**지원자 모범 답변**:
> "먼저 SPI 프로토콜 스펙을 분석하여 인터페이스 신호와 프로토콜 규칙을 정리합니다. 다음으로 `spi_seq_item`을 정의하여 MOSI/MISO 데이터, 클록 극성(CPOL), 클록 위상(CPHA) 등을 필드로 선언합니다.
>
> 그 다음 SPI Agent를 구축합니다. Driver는 SPI 프로토콜에 맞게 SCK, MOSI 신호를 구동하고, Monitor는 MISO를 관찰하여 트랜잭션을 재구성합니다. Scoreboard는 전송한 데이터와 수신한 데이터를 비교합니다.
>
> Smoke test로 기본 송수신을 검증한 후, CPOL/CPHA 4가지 모드, 다양한 데이터 길이, 연속 전송 등의 시나리오를 추가합니다. Coverage는 모드별, 데이터 크기별, 에러 조건별로 정의하고, Assertion으로 SCK 타이밍과 CS 활성화 규칙을 검증합니다."

---

**면접관**: 시뮬레이션 중 Scoreboard에서 mismatch가 발생했는데, DUT 버그인지 테스트벤치 버그인지 어떻게 구분하시겠습니까?

**지원자 모범 답변**:
> "먼저 파형을 확인하여 DUT 인터페이스의 실제 신호를 봅니다. Monitor가 캡처한 트랜잭션과 실제 신호가 일치하는지 확인합니다. 만약 Monitor가 잘못 캡처했다면 테스트벤치 버그이고, 신호 자체가 잘못되었다면 DUT 버그입니다.
>
> 다음으로 Scoreboard의 참조 모델 로직을 검증합니다. 단순한 케이스(주소 0에 0xFF 쓰고 읽기)로 Scoreboard 동작을 확인합니다. 참조 모델이 정확한데 mismatch가 나면 DUT 버그입니다.
>
> 최종적으로 시뮬레이터의 wave dump 기능으로 DUT 내부 신호를 추적하여 어느 시점에서 데이터가 달라지는지 찾습니다."

---

**면접관**: 마지막으로 질문 있으신가요?

> 💡 **팁**: 반드시 질문을 준비하세요! 좋은 질문 예시:

| 좋은 질문 | 인상 |
|----------|------|
| "팀에서 주로 사용하는 프로토콜과 VIP는 무엇인가요?" | 실무 관심 |
| "신입에게 기대하는 첫 3개월 목표가 있나요?" | 적극적 자세 |
| "코드 리뷰 문화가 있나요?" | 성장 의지 |
| "커버리지 클로저 목표는 보통 몇 %인가요?" | 전문성 |

### 15.6.3 면접 후 팔로업

면접이 끝난 후에도 해야 할 일이 있습니다:

1. **감사 이메일** (당일 또는 다음 날):
   - 면접 기회에 대한 감사
   - 면접에서 논의한 핵심 주제 언급
   - 팀에 기여하고 싶다는 의지

2. **처우 협의 준비**:

| 항목 | 확인 사항 |
|------|-----------|
| 연봉 | 업계 평균 확인 (반도체 검증 신입 기준) |
| 성과급 | 연봉 외 보너스 구조 |
| 교육 지원 | 학회, 교육, 자격증 지원 여부 |
| 장비 | 개발 환경, 시뮬레이터 라이선스 |
| 성장 경로 | 시니어 엔지니어 → 팀 리드 경로 |

---

## 15.7 체크포인트

> **이 절의 목표**: 면접 준비 상태를 점검하고, 전체 책 학습을 마무리합니다.

### 15.7.1 셀프 체크

다음 질문에 자신 있게 답할 수 있는지 확인하세요:

| 번호 | 질문 | 자신감 |
|------|------|--------|
| 1 | Factory Pattern의 목적과 create()를 쓰는 이유를 설명할 수 있는가? | ☐ |
| 2 | UVM Phase의 종류와 build/connect/run의 차이를 설명할 수 있는가? | ☐ |
| 3 | Analysis Port의 1:N 브로드캐스트 동작을 설명할 수 있는가? | ☐ |
| 4 | UVM 코드를 보고 3가지 이상의 문제를 찾을 수 있는가? | ☐ |
| 5 | 포트폴리오 프로젝트의 핵심 기술을 3분 안에 설명할 수 있는가? | ☐ |
| 6 | Coverage Closure 프로세스를 단계별로 설명할 수 있는가? | ☐ |

> 6개 모두 체크했다면 **면접 준비 완료**입니다!

### 15.7.2 연습문제

**문제 1 (쉬움): 면접 답변 작성**

다음 질문에 대해 "핵심 → 이유 → 예시" 구조로 답변을 작성하세요:
"UVM에서 Sequence와 Transaction의 차이는 무엇인가요?"

<details>
<summary>모범 답안 보기</summary>

Transaction(`uvm_sequence_item`)은 **데이터의 단위**이고, Sequence(`uvm_sequence`)는 **여러 Transaction을 순서대로 생성하는 시나리오**입니다. Transaction이 "편지 한 장"이라면, Sequence는 "편지를 쓰는 과정(초안→수정→발송)"입니다.

예를 들어 APB 쓰기 트랜잭션에는 주소와 데이터가 들어있고, APB 쓰기 시퀀스는 이 트랜잭션을 10번 반복 생성하여 연속 쓰기 테스트를 수행합니다.

참고: Transaction은 `` `uvm_object_utils``로 등록하고, Sequence도 `` `uvm_object_utils``로 등록합니다 — 둘 다 `uvm_object` 계열입니다.
</details>

**문제 2 (보통): 코드 리뷰 연습**

다음 코드에서 문제점을 모두 찾고 수정하세요:

```systemverilog
class apb_monitor extends uvm_monitor;
  virtual apb_if vif;
  uvm_analysis_port #(apb_seq_item) ap;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual task run_phase(uvm_phase phase);
    apb_seq_item item;
    forever begin
      @(posedge vif.clk iff vif.psel);
      item = new("item");
      item.paddr  = vif.paddr;
      item.pwdata = vif.pwdata;
      item.pwrite = vif.pwrite;
      ap.write(item);
    end
  endtask
endclass
```

<details>
<summary>정답 보기</summary>

1. **`` `uvm_component_utils `` 누락** — Factory 미등록 (Monitor는 component이므로 `uvm_component_utils`)
2. **`build_phase` 없음** — `ap`를 생성하지 않음, `vif`를 `config_db`에서 가져오지 않음
3. **`item = new("item")` → `create()` 사용** — Factory를 통해 생성해야 함
4. **APB Access phase 미대기** — `psel` 후 `penable`이 올라가는 Access phase 완료를 기다려야 실제 데이터를 캡처
5. **읽기 시 `prdata` 캡처 누락** — `pwrite==0`일 때 `prdata`도 캡처해야 함

```systemverilog
class apb_monitor extends uvm_monitor;
  `uvm_component_utils(apb_monitor)  // (1) Factory 등록
  virtual apb_if vif;
  uvm_analysis_port #(apb_seq_item) ap;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);  // (2) build_phase 추가
    super.build_phase(phase);
    ap = new("ap", this);
    if (!uvm_config_db#(virtual apb_if)::get(this, "", "vif", vif))
      `uvm_fatal(get_type_name(), "vif not found")
  endfunction

  virtual task run_phase(uvm_phase phase);
    apb_seq_item item;
    forever begin
      @(posedge vif.clk iff (vif.psel && vif.penable));  // (4) Access phase
      item = apb_seq_item::type_id::create("item");       // (3) Factory
      item.paddr  = vif.paddr;
      item.pwdata = vif.pwdata;
      item.pwrite = vif.pwrite;
      if (!vif.pwrite) item.prdata = vif.prdata;           // (5) 읽기 데이터
      ap.write(item);
    end
  endtask
endclass
```
</details>

**문제 3 (어려움): 포트폴리오 README 작성**

Ch.11~14에서 만든 APB 검증 환경에 대한 GitHub README.md를 직접 작성하세요. 다음 항목을 포함해야 합니다:
- 프로젝트 개요 (3문장)
- 아키텍처 다이어그램 (ASCII)
- 주요 기능 (5개 이상)
- 검증 결과 (숫자 포함)
- 실행 방법

<details>
<summary>모범 답안 보기</summary>

15.4.2의 README 템플릿을 참고하여, 자신만의 문장으로 재구성하세요. 핵심은 **숫자**와 **구체적 기술 용어**입니다.
</details>

### 15.7.3 이 챕터에서 배운 것

이 챕터에서 준비한 취업 관련 자료:

```
면접 & 포트폴리오 준비 현황
├── 면접 대비
│   ├── UVM 빈출 질문 30선 + 모범 답안
│   ├── 코드 리뷰 문제 3세트 (쉬움/보통/어려움)
│   └── 면접 시뮬레이션 2세트 (1차/2차)
├── 포트폴리오
│   ├── GitHub 저장소 구조 + README 템플릿
│   ├── 검증 계획서 템플릿
│   └── 커버리지 결과 요약 가이드
└── 이력서/자소서
    ├── 필수 키워드 목록
    ├── 성과 표현 공식
    └── STAR 기법 가이드
```

### 15.7.4 전체 책 마무리 — Ch.1~15 학습 로드맵

축하합니다! 15개 챕터를 모두 마쳤습니다. 여기까지 온 여러분의 여정을 되돌아봅시다:

```
Ch.1~15 전체 학습 로드맵

Part 1: 시작하기
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ Ch.1    │  │ Ch.2    │  │ Ch.3    │  │ Ch.4    │  │ Ch.5    │
│ UVM     │─▶│ 환경    │─▶│ System  │─▶│ UVM     │─▶│ 첫 TB   │
│ 소개    │  │ 설정    │  │ Verilog │  │ 기본    │  │ 작성    │
│         │  │         │  │         │  │ 컴포넌트│  │         │
└─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘

Part 2: 깊이 파기
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ Ch.6    │  │ Ch.7    │  │ Ch.8    │  │ Ch.9    │  │ Ch.10   │
│ 시퀀스  │─▶│ Driver  │─▶│ Score   │─▶│ 테스트  │─▶│ 디버깅  │
│ &시퀀서 │  │ &Monitor│  │ board   │  │ 시나리오│  │ 기법    │
└─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘

Part 3: 완성하기
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐
│ Ch.11   │  │ Ch.12   │  │ Ch.13   │  │ Ch.14   │  │ Ch.15    │
│ 인터    │─▶│ RAL     │─▶│ 고급    │─▶│ 검증    │─▶│ 면접 &   │
│ 페이스  │  │         │  │ 시퀀스  │  │ 자동화  │  │ 포트폴리오│
└─────────┘  └─────────┘  └─────────┘  └─────────┘  └──────────┘
                                                       지금 여기!
```

**Part 1에서 배운 것 — "기초 체력 만들기"**: UVM이 무엇인지 이해하고(Ch.1), 개발 환경을 설정하고(Ch.2), SystemVerilog 핵심 문법을 익히고(Ch.3), UVM 기본 컴포넌트의 동작 원리를 배우고(Ch.4), 처음으로 완전한 테스트벤치를 만들었습니다(Ch.5).

**Part 2에서 배운 것 — "기술 하나하나 깊이 파기"**: Sequence로 테스트 시나리오를 설계하고(Ch.6), Driver와 Monitor로 DUT와 소통하고(Ch.7), Scoreboard로 자동 비교하고(Ch.8), Constrained Random으로 다양한 테스트를 작성하고(Ch.9), 디버깅 기법으로 문제를 해결하는 능력을 갖추었습니다(Ch.10).

**Part 3에서 배운 것 — "실무 수준으로 완성하기"**: APB 에이전트를 구축하고(Ch.11), RAL로 레지스터를 추상화하고(Ch.12), Virtual Sequence로 복잡한 시나리오를 조율하고(Ch.13), Coverage와 Assertion으로 검증 완전성을 확보하고(Ch.14), 이 모든 것을 면접과 포트폴리오에 담는 방법을 배웠습니다(Ch.15).

**이 책을 완독한 여러분은:**

- [x] UVM 테스트벤치를 처음부터 구축할 수 있습니다
- [x] 커버리지 기반 검증 방법론을 이해하고 적용할 수 있습니다
- [x] 면접에서 UVM 질문에 자신 있게 답할 수 있습니다
- [x] GitHub 포트폴리오로 역량을 증명할 수 있습니다
- [x] 팹리스 검증 엔지니어로 첫 걸음을 내딛을 준비가 되었습니다

> 이 책의 목표는 "초보자도 따라하면 팹리스 검증 엔지니어로 취업할 수 있는 실전 UVM 교재"였습니다. 15개 챕터를 통해 그 여정을 함께 했습니다. 이제 남은 것은 **실행**입니다. 포트폴리오를 GitHub에 올리고, 이력서를 준비하고, 면접에 도전하세요. 여러분은 이미 충분히 준비되어 있습니다.
