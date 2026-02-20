# Chapter 1: UVM 소개

> **학습 목표**
> - UVM이 무엇이고 왜 필요한지 이해한다
> - UVM 테스트벤치(Testbench)의 기본 구조를 파악한다
> - 실습 환경(EDA Playground)을 설정하고 첫 UVM 코드를 실행한다
> - 트랜잭션(Transaction)의 개념을 이해하고 랜덤 데이터 생성을 체험한다

---

## 1.1 UVM이란 무엇인가?

### 1.1.1 검증이 왜 필요한가?

반도체 칩 하나를 설계하면, 그 칩이 **정말로 의도한 대로 동작하는지** 확인해야 합니다. 이 과정을 **검증(Verification)**이라고 합니다.

실제 팹리스(Fabless) 회사에서는 전체 개발 시간의 **60~70% 이상이 검증**에 사용됩니다. 왜 그럴까요?

| 단계 | 설명 | 비용 |
|------|------|------|
| RTL 설계 | Verilog/VHDL로 회로 작성 | 낮음 |
| 시뮬레이션 검증 | 테스트벤치(Testbench)로 동작 확인 | 중간 |
| 실리콘 제조 (Tape-out) | 실제 칩 생산 | **매우 높음** |
| 버그 발견 시 재설계 | 처음부터 다시 | **치명적** |

> **핵심**: 테이프아웃(Tape-out) 이후에 버그를 발견하면 수억~수십억 원의 손실이 발생합니다. 그래서 시뮬레이션 단계에서 최대한 많은 버그를 잡아야 합니다.

### 1.1.2 전통적 검증 vs UVM 검증

초기에는 Verilog로 직접 테스트벤치(Testbench)를 작성했습니다:

```systemverilog
// 전통적 방식: 직접 신호를 넣고 결과를 눈으로 확인
// (의도적으로 구식 Verilog 스타일로 작성한 예제입니다)
module tb_adder;
  reg [7:0] a, b;       // 입력 신호
  wire [8:0] sum;        // 출력 신호

  // DUT(Device Under Test, 검증 대상) 연결
  adder dut (.a(a), .b(b), .sum(sum));

  initial begin
    // 테스트 케이스 하나하나 수동으로 작성
    a = 8'd10; b = 8'd20;
    #10;
    if (sum !== 9'd30) $display("ERROR: 10+20 != 30");

    a = 8'd255; b = 8'd1;
    #10;
    if (sum !== 9'd256) $display("ERROR: 255+1 != 256");

    // ... 수백 개의 케이스를 일일이 작성해야 합니다
    $finish;
  end
endmodule
```

이 방식의 **문제점**:

| 문제 | 설명 |
|------|------|
| 수동 작성 | 테스트 케이스를 하나하나 직접 작성 -> 시간 소모 |
| 재사용 불가 | 프로젝트마다 처음부터 새로 작성 |
| 커버리지 측정 어려움 | 얼마나 검증했는지 정량적으로 알 수 없음 |
| 팀 협업 어려움 | 각자 다른 스타일로 작성 -> 유지보수 곤란 |

> **한마디로**: 프로젝트 규모가 커질수록 전통적 방식으로는 한계에 부딪힙니다. 이 문제를 해결하기 위해 UVM이 등장했습니다.

### 1.1.3 UVM의 등장

**UVM (Universal Verification Methodology)**은 이런 문제를 해결하기 위해 만들어진 **표준화된 검증 방법론**입니다.

```
UVM = SystemVerilog 기반 + 표준 라이브러리 + 검증 방법론
```

처음에는 EDA 회사마다 자기만의 검증 방법론을 만들어 사용했는데, 결국 업계가 하나로 통합한 것이 UVM입니다:

```
eRM (Verisity) -> VMM (Synopsys) -> OVM (Mentor+Cadence) -> UVM (업계 통합 표준)
 [각 회사별 독자 방법론]                                        ^
                                                          지금 배우는 것!
```

> 각 방법론의 약자가 궁금하다면: eRM = e Reuse Methodology, VMM = Verification Methodology Manual, OVM = Open Verification Methodology. 지금은 이름만 알면 충분합니다.

**UVM의 핵심 특징**:

| 특징 | 설명 | 실무 이점 |
|------|------|-----------|
| **표준화** | IEEE에서 관리하는 IEEE 1800.2 표준 (Accellera에서 레퍼런스 구현 제공) | 어떤 회사든 같은 방식 |
| **재사용성** | 컴포넌트를 모듈처럼 조립 | 프로젝트 간 코드 공유 |
| **자동화** | 랜덤 생성 + 자동 체크 | 적은 코드로 많은 검증 |
| **확장성** | 필요에 따라 커스터마이즈 | 단순~복잡 모두 대응 |
| **커버리지** | 기능/코드 커버리지(Coverage) 내장 | 검증 완료 판단 가능 |

### 1.1.4 UVM 테스트벤치(Testbench) 구조 한눈에 보기

```
┌─────────────────────────────────────────────────────┐
│                    UVM Test                          │
│  ┌────────────────────────────────────────────────┐  │
│  │              UVM Environment                    │  │
│  │  ┌─────────────────┐  ┌──────────┐            │  │
│  │  │  Active Agent    │  │Scoreboard│            │  │
│  │  │ ┌─────────────┐ │  │          │            │  │
│  │  │ │  Sequencer   │ │  │ 예상값과 │            │  │
│  │  │ │  Driver      │ │  │ 실제값   │            │  │
│  │  │ │  Monitor     │ │  │ 비교     │            │  │
│  │  │ └─────────────┘ │  │          │            │  │
│  │  └─────────────────┘  └──────────┘            │  │
│  └────────────────────────────────────────────────┘  │
│                        │                              │
│              ┌─────────┴──────────┐                  │
│              │ Virtual Interface   │                  │
│              └─────────┬──────────┘                  │
│                        │                              │
└────────────────────────┼─────────────────────────────┘
                         │
                ┌────────┴────────┐
                │   DUT (설계)     │
                │   검증 대상      │
                └─────────────────┘
```

각 컴포넌트의 역할을 간단히 정리하면:

| 컴포넌트 | 역할 | 비유 |
|----------|------|------|
| **테스트(Test)** | 전체 테스트 시나리오 정의 | 감독 |
| **환경(Environment)** | 컴포넌트들을 묶는 컨테이너 | 영화 세트장 |
| **에이전트(Agent)** | 시퀀서 + 드라이버 + 모니터 묶음 | 촬영팀 |
| **시퀀서(Sequencer)** | 테스트 데이터(시퀀스) 생성/관리 | 대본 작가 |
| **드라이버(Driver)** | 데이터를 DUT 핀에 전달 | 배우 |
| **모니터(Monitor)** | DUT의 동작을 관찰/기록 | 카메라 |
| **스코어보드(Scoreboard)** | 예상 결과와 실제 결과 비교 | 편집자 |
| **가상 인터페이스(Virtual Interface)** | UVM 코드(클래스)와 DUT(모듈)를 연결하는 통로 | 무대와 객석을 잇는 통로 |

> **지금은 이 그림을 "아, 이런 구조구나" 정도로만 이해하세요.** 각 컴포넌트는 Chapter 4~8에서 하나씩 자세히 배웁니다.

---

## 1.2 왜 UVM을 배워야 하는가?

### 1.2.1 취업 시장에서의 UVM

팹리스(Fabless) 검증 엔지니어(Verification Engineer) 채용 공고를 보면:

```
[채용 공고 예시 - 팹리스 검증 엔지니어]

필수 자격:
- SystemVerilog 기반 UVM 검증 경험
- 기능 커버리지(Functional Coverage) 및 코드 커버리지(Code Coverage) 분석 경험
- 프로토콜 검증 경험 (AXI, APB, UART 등)

우대 사항:
- UVM RAL(Register Abstraction Layer) 경험
- SystemVerilog Assertion (SVA) 활용 능력
- VIP(Verification IP) 사용 경험
```

거의 **모든 팹리스/반도체 회사**에서 UVM을 요구합니다:

- **국내**: 삼성전자, SK하이닉스, 텔레칩스, 넥스트칩, 실리콘웍스, LX세미콘 등
- **해외**: 퀄컴(Qualcomm), 엔비디아(NVIDIA), AMD, 인텔(Intel) 등

### 1.2.2 UVM을 배우면 얻는 것

```
 UVM 학습
    │
    ├── 체계적인 검증 사고방식
    │     └─ "어떻게 버그를 찾을까?"를 구조적으로 접근
    │
    ├── 재사용 가능한 코드 작성 능력
    │     └─ OOP(객체지향) + 디자인 패턴 실력 향상
    │
    ├── 팀 협업 능력
    │     └─ 표준 방법론으로 팀원과 원활한 소통
    │
    └── 커리어 확장
          ├─ 검증 엔지니어 (Verification Engineer)
          ├─ DV 리드 (Design Verification Lead)
          └─ 검증 아키텍트 (Verification Architect)
```

### 1.2.3 이 책의 학습 로드맵

이 책은 총 15개 Chapter를 3개 Part로 나누어 단계별로 학습합니다:

```
Part 1: 시작하기 (Chapter 1-5)
━━━━━━━━━━━━━━━━━━━━━━━━━
Ch.1  UVM 소개                  <-- 지금 여기!
Ch.2  환경 설정
Ch.3  SystemVerilog 핵심
Ch.4  UVM 기본 컴포넌트
Ch.5  첫 UVM 테스트벤치(Testbench)

Part 2: 깊이 파기 (Chapter 6-10)
━━━━━━━━━━━━━━━━━━━━━━━━━
Ch.6  시퀀스(Sequence) & 시퀀서(Sequencer)
Ch.7  드라이버(Driver) & 모니터(Monitor)
Ch.8  스코어보드(Scoreboard) & 커버리지(Coverage)
Ch.9  테스트 시나리오
Ch.10 디버깅 기법

Part 3: 완성하기 (Chapter 11-15)
━━━━━━━━━━━━━━━━━━━━━━━━━
Ch.11 레지스터 모델(Register Model, RAL)
Ch.12 VIP 활용
Ch.13 고급 시퀀스 기법
Ch.14 실전 프로젝트
Ch.15 면접 준비 & 포트폴리오
```

> **Tip**: 각 Chapter는 "이론 30% + 실습 70%"로 구성됩니다. 반드시 직접 코드를 실행해 보면서 학습하세요.

---

## 1.3 실습 환경 구성

> **이 절의 목표**: 이번 절을 마치면, UVM 코드를 직접 실행할 수 있는 환경이 준비됩니다.

### 1.3.1 필요한 도구들

UVM을 실습하려면 **EDA 시뮬레이터**가 필요합니다. 아래 표에서 자신에게 맞는 도구를 확인하세요:

| 도구 | 종류 | 비용 | 추천 대상 |
|------|------|------|-----------|
| **EDA Playground** | 온라인 | **무료** | **초보자 강력 추천** |
| Synopsys VCS | 상용 | 유료 | 업계 표준 (회사/대학 라이선스) |
| Cadence Xcelium | 상용 | 유료 | 업계 표준 (회사/대학 라이선스) |
| Siemens Questa (구 Mentor) | 상용 | 유료 | 업계 표준 (회사/대학 라이선스) |

> **초보자 추천**: 설치 없이 바로 사용 가능한 [EDA Playground](https://www.edaplayground.com)로 시작하세요! 이 책의 모든 예제는 EDA Playground에서 실행 가능합니다.

### 1.3.2 EDA Playground 시작하기

지금 바로 실습 환경을 설정해 봅시다.

**Step 1**: https://www.edaplayground.com 에 접속하여 회원가입합니다.

**Step 2**: 시뮬레이터를 설정합니다.
```
왼쪽 패널에서:
  Tools & Simulators --> Aldec Riviera Pro (추천) 또는 Synopsys VCS 선택

  [체크] UVM/OVM
  UVM Version --> 가능한 최신 버전 선택
```

> **시뮬레이터 선택 팁**: 이 책의 예제는 **Aldec Riviera Pro**에서 테스트되었습니다. 같은 시뮬레이터를 선택하면 결과가 가장 일치합니다. 어떤 것을 선택해도 UVM 코드 자체는 동일하게 동작하므로, 사용 가능한 것 아무거나 선택해도 괜찮습니다.

**Step 3**: 코드 입력 영역을 확인합니다.
```
왼쪽 편집기: testbench.sv  (테스트벤치 코드를 여기에 작성)
오른쪽 편집기: design.sv   (설계 코드를 여기에 작성)
```

**Step 4**: 상단의 **Run** 버튼을 클릭하면 시뮬레이션이 실행됩니다!

**Step 5 (확인)**: 하단 로그 창에 `UVM_INFO`로 시작하는 메시지가 출력되면 환경 설정이 올바르게 된 것입니다.

### 1.3.3 로컬 환경 설정 (선택사항)

> **참고**: 이 절은 회사나 대학에서 VCS 라이선스를 보유한 경우를 위한 내용입니다. EDA Playground를 사용하는 분은 건너뛰어도 됩니다.

VCS를 사용할 수 있는 환경이라면 다음과 같이 설정합니다:

```bash
# 1. UVM 라이브러리 경로 확인
echo $UVM_HOME
# 예: /tools/synopsys/vcs/etc/uvm-1.2

# 2. 작업 디렉토리 생성
mkdir -p ~/uvm_practice/ch01
cd ~/uvm_practice/ch01

# 3. 간단한 Makefile 작성
cat > Makefile << 'EOF'
# =============================================
# UVM 실습용 Makefile
# 사용법: make run TEST=hello_test FILES=hello_uvm.sv
# =============================================
UVM_HOME ?= /tools/synopsys/vcs/etc/uvm-1.2
VCS = vcs

# 컴파일 옵션
VCS_OPTS = -sverilog \
           -ntb_opts uvm-1.2 \
           +incdir+$(UVM_HOME)/src \
           $(UVM_HOME)/src/uvm.sv \
           -timescale=1ns/1ps \
           +UVM_VERBOSITY=UVM_MEDIUM

# 실행
run: compile
	./simv +UVM_TESTNAME=$(TEST)

# 컴파일
compile:
	$(VCS) $(VCS_OPTS) -o simv $(FILES)

# 정리
clean:
	rm -rf simv simv.daidir csrc *.log *.vpd ucli.key

.PHONY: run compile clean
EOF
```

이제 실습 환경이 준비되었으니, 드디어 첫 번째 UVM 코드를 작성해 봅시다!

---

## 1.4 첫 번째 UVM 예제

### 1.4.1 "Hello UVM!" - 가장 간단한 UVM 프로그램

드디어 첫 번째 UVM 코드를 작성합니다! 복잡한 것은 나중에 배울 테니, 먼저 가장 기본적인 구조부터 익혀 봅시다.

**[예제 1-1] hello_uvm.sv**

```systemverilog
// ============================================
// 예제 1-1: Hello UVM!
// 목적: UVM의 가장 기본적인 구조 이해
// 파일: hello_uvm.sv
// ============================================

// UVM 라이브러리 포함 (항상 이 두 줄로 시작!)
`include "uvm_macros.svh"    // UVM 매크로 정의
import uvm_pkg::*;            // UVM 패키지 임포트

// ----------------------------------------
// UVM 테스트(Test) 클래스 정의
// - uvm_test를 상속받아야 합니다
// - UVM 테스트벤치(Testbench)의 최상위 컴포넌트
// ----------------------------------------
class hello_test extends uvm_test;

  // UVM 팩토리(Factory)에 이 클래스를 등록
  // (나중에 자세히 배울 예정, 지금은 "필수 주문" 정도로 이해)
  `uvm_component_utils(hello_test)

  // 생성자 (UVM 컴포넌트는 항상 이 형태의 생성자가 필요)
  // 참고: uvm_test에서는 parent = null이 허용되지만,
  //       일반 컴포넌트에서는 반드시 parent를 지정해야 합니다.
  function new(string name = "hello_test", uvm_component parent = null);
    super.new(name, parent);  // 부모 클래스 생성자 호출
  endfunction

  // ----------------------------------------
  // build_phase: 테스트벤치(Testbench) 구성 단계
  // - 컴포넌트 생성 및 설정을 수행
  // - UVM이 자동으로 호출해줌
  // ----------------------------------------
  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    `uvm_info("BUILD", "테스트벤치를 구성하고 있습니다!", UVM_MEDIUM)
  endfunction

  // ----------------------------------------
  // run_phase: 실제 테스트 실행 단계
  // - 시뮬레이션이 여기서 동작
  // - task이므로 시간 소모 가능 (#delay 등)
  // ----------------------------------------
  virtual task run_phase(uvm_phase phase);
    // 오브젝션(Objection): "아직 시뮬레이션 끝내지 마세요!" 신호
    // 중요: raise_objection은 반드시 run_phase 시작 부분에서 호출하세요!
    phase.raise_objection(this);

    `uvm_info("RUN", "========================================", UVM_MEDIUM)
    `uvm_info("RUN", "  안녕하세요! 첫 번째 UVM 테스트입니다!", UVM_MEDIUM)
    `uvm_info("RUN", "  UVM 세계에 오신 것을 환영합니다!    ", UVM_MEDIUM)
    `uvm_info("RUN", "========================================", UVM_MEDIUM)

    // 100ns 대기 (시뮬레이션 시간)
    #100;

    `uvm_info("RUN", "100ns가 경과했습니다. 테스트를 종료합니다.", UVM_MEDIUM)

    // 오브젝션(Objection) 해제: "이제 끝내도 됩니다" 신호
    phase.drop_objection(this);
  endtask

  // ----------------------------------------
  // report_phase: 결과 보고 단계
  // - 테스트 결과 요약 출력
  // ----------------------------------------
  virtual function void report_phase(uvm_phase phase);
    `uvm_info("REPORT", "테스트가 성공적으로 완료되었습니다!", UVM_MEDIUM)
  endfunction

endclass

// ----------------------------------------
// 최상위 모듈 (시뮬레이션 진입점)
// ----------------------------------------
module top;
  initial begin
    // UVM 테스트 실행!
    // "hello_test" 클래스를 찾아서 자동으로 실행
    run_test("hello_test");
    // 참고: 실무에서는 run_test()를 인자 없이 호출하고
    // 커맨드라인에서 +UVM_TESTNAME=hello_test 로 지정하는 방식이 더 일반적입니다.
  end
endmodule
```

### 1.4.2 코드 분석: 한 줄 한 줄 이해하기

위 코드의 핵심 포인트를 하나씩 짚어 봅시다.

**1) UVM 시작 선언 (2줄)**

```systemverilog
`include "uvm_macros.svh"    // 매크로 모음 (`uvm_info 등)
import uvm_pkg::*;            // UVM 클래스 라이브러리
```

> 모든 UVM 파일에서 이 두 줄은 **필수**입니다. 외워두세요!

**2) 클래스 상속**

```systemverilog
class hello_test extends uvm_test;
```

> UVM은 **객체지향(OOP, Object-Oriented Programming)**을 기반으로 합니다. `uvm_test`를 상속받아 나만의 테스트를 만듭니다. 객체지향이 낯설더라도 걱정 마세요 -- Chapter 3에서 SystemVerilog의 OOP를 상세히 다룹니다.

**3) 팩토리(Factory) 등록**

```systemverilog
`uvm_component_utils(hello_test)
```

> UVM 팩토리(Factory)는 "클래스 등록부"입니다. 등록해야 UVM이 이 클래스를 인식하고 사용할 수 있습니다. 자세한 내용은 Chapter 4에서 다룹니다.

**4) 페이즈(Phase) - UVM의 실행 단계**

UVM은 정해진 순서(페이즈, Phase)대로 자동 실행됩니다. 우리는 각 페이즈에 할 일만 작성하면 됩니다!

주요 페이즈(Phase):
```
build_phase     --> 구성 단계 (컴포넌트 생성)
connect_phase   --> 연결 단계 (컴포넌트 간 포트 연결)
run_phase       --> 실행 단계 (시뮬레이션 동작, 유일한 task phase)
report_phase    --> 보고 단계 (결과 출력)
```

아래는 UVM 페이즈(Phase)의 **전체 실행 순서**입니다 (총 9개):

```
  ┌─────────────────────┐
  │    build_phase       │  컴포넌트 생성
  └──────────┬──────────┘
             v
  ┌─────────────────────┐
  │   connect_phase      │  컴포넌트 간 포트 연결
  └──────────┬──────────┘
             v
  ┌─────────────────────┐
  │ end_of_elaboration   │  구성 완료 확인
  └──────────┬──────────┘
             v
  ┌─────────────────────┐
  │ start_of_simulation  │  시뮬레이션 시작 전 준비
  └──────────┬──────────┘
             v
  ╔═════════════════════╗
  ║     run_phase        ║  << 실제 시뮬레이션 (시간 소모 가능)
  ╚══════════╤══════════╝
             v
  ┌─────────────────────┐
  │   extract_phase      │  결과 수집
  └──────────┬──────────┘
             v
  ┌─────────────────────┐
  │    check_phase       │  결과 검증
  └──────────┬──────────┘
             v
  ┌─────────────────────┐
  │   report_phase       │  최종 보고
  └──────────┬──────────┘
             v
  ┌─────────────────────┐
  │    final_phase       │  마무리 정리
  └─────────────────────┘
```

> **task vs function 차이점**
> | 구분 | `task` | `function` |
> |------|--------|------------|
> | 시간 소모 | `#100` 같은 지연 **가능** | 0 시간에 즉시 완료해야 함 |
> | UVM에서 | `run_phase`만 task | 나머지 8개 phase는 모두 function |
> | 기억법 | "**실행**은 시간이 걸린다" | "**설정/보고**는 순간적이다" |
>
> 이 구분은 나중에 매우 중요하므로, `run_phase = task`라는 것만 확실히 기억하세요!

**5) 오브젝션(Objection) 메커니즘**

```systemverilog
phase.raise_objection(this);  // "아직 끝내지 마!"
// ... 테스트 로직 ...
phase.drop_objection(this);   // "이제 끝내도 돼"
```

> 모든 오브젝션(Objection)이 해제(drop)되면 시뮬레이션이 자동 종료됩니다. 만약 `raise_objection` 없이 `run_phase`를 작성하면, 시뮬레이션이 바로 끝나버립니다!

> **주의**: `raise_objection`은 반드시 `run_phase` 시작 부분에서 호출하세요. `#delay` 이후에 호출하면, 다른 컴포넌트가 이미 오브젝션을 해제하여 시뮬레이션이 먼저 종료될 수 있습니다.

**6) `uvm_info` 메시지 매크로**

```systemverilog
`uvm_info(TAG, MESSAGE, VERBOSITY)
// TAG:       메시지 분류 태그 (필터링에 사용)
// MESSAGE:   출력할 문자열
// VERBOSITY: 출력 레벨
```

UVM은 메시지 출력을 위한 전용 매크로를 제공합니다:

| 매크로 | 용도 | 심각도 |
|--------|------|--------|
| `` `uvm_info `` | 정보 메시지 출력 | 낮음 (정보) |
| `` `uvm_warning `` | 경고 메시지 출력 | 중간 (경고) |
| `` `uvm_error `` | 에러 메시지 출력 | 높음 (에러) |
| `` `uvm_fatal `` | 치명적 에러 (시뮬레이션 즉시 종료) | 최고 (치명적) |

Verbosity(출력 상세 수준) 레벨:

| 레벨 | 값 | 용도 |
|------|-----|------|
| `UVM_NONE` | 0 | 항상 출력 |
| `UVM_LOW` | 100 | 최소 정보 |
| `UVM_MEDIUM` | 200 | 기본 수준 (가장 많이 사용) |
| `UVM_HIGH` | 300 | 상세 정보 |
| `UVM_FULL` | 400 | 최대 상세 |

> `$display` 대신 `uvm_info`를 사용하면, UVM이 자동으로 시간/위치/심각도를 관리해 줍니다.

### 1.4.3 실행 결과

위 코드를 실행하면 아래와 같은 결과가 출력됩니다:

```
UVM_INFO @ 0: reporter [RNTST] Running test hello_test...
UVM_INFO hello_uvm.sv(35) @ 0: uvm_test_top [BUILD] 테스트벤치를 구성하고 있습니다!
UVM_INFO hello_uvm.sv(44) @ 0: uvm_test_top [RUN] ========================================
UVM_INFO hello_uvm.sv(45) @ 0: uvm_test_top [RUN]   안녕하세요! 첫 번째 UVM 테스트입니다!
UVM_INFO hello_uvm.sv(46) @ 0: uvm_test_top [RUN]   UVM 세계에 오신 것을 환영합니다!
UVM_INFO hello_uvm.sv(47) @ 0: uvm_test_top [RUN] ========================================
UVM_INFO hello_uvm.sv(52) @ 100: uvm_test_top [RUN] 100ns가 경과했습니다. 테스트를 종료합니다.
UVM_INFO hello_uvm.sv(60) @ 100: uvm_test_top [REPORT] 테스트가 성공적으로 완료되었습니다!

--- UVM Report Summary ---
** Report counts by severity
UVM_INFO :    8
UVM_WARNING :    0
UVM_ERROR :    0
UVM_FATAL :    0
** Report counts by id
[BUILD] :    1
[REPORT] :    1
[RNTST] :    1
[RUN] :    5
```

**실행 결과 읽는 법**:

| 출력 요소 | 의미 |
|-----------|------|
| `UVM_INFO` | 메시지 심각도 (정보) |
| `hello_uvm.sv(35)` | 소스 파일명과 줄 번호 |
| `@ 0`, `@ 100` | 시뮬레이션 시간 (ns) |
| `uvm_test_top` | UVM이 자동으로 붙인 최상위 인스턴스 이름 |
| `[BUILD]`, `[RUN]` | 우리가 지정한 태그(TAG) |
| **Report Summary** | UVM이 자동으로 출력하는 메시지 통계 |

> **핵심**: `UVM_ERROR`와 `UVM_FATAL`이 0이면 테스트가 성공적으로 통과한 것입니다!
>
> **참고**: 실행 결과의 줄 번호(예: `hello_uvm.sv(35)`)는 사용하는 시뮬레이터나 코드 복사 방식에 따라 다를 수 있습니다. 줄 번호가 다르더라도 메시지 내용이 동일하면 정상입니다.

### 1.4.4 실습: 직접 해보기!

> **중요**: 코드를 눈으로만 읽지 말고, 반드시 직접 실행해 보세요. 직접 실행하고 결과를 확인하는 것이 가장 빠른 학습 방법입니다.

**[실습 1-1] Hello UVM 실행하기**

1. [EDA Playground](https://www.edaplayground.com)에 접속합니다.
2. 1.3.2절에서 설명한 대로 시뮬레이터를 설정합니다.
3. 왼쪽 testbench.sv에 예제 1-1의 코드를 복사합니다.
4. 오른쪽 design.sv는 비워둡니다 (이 예제에서는 DUT가 불필요).
5. **Run** 버튼을 클릭합니다!
6. **확인**: 하단 로그에 `UVM Report Summary`가 표시되면 성공입니다.

**[실습 1-2] 메시지 수정해보기**

`uvm_info`의 메시지를 자신만의 내용으로 바꿔보세요:

```systemverilog
// 아래 부분을 여러분만의 메시지로 수정해보세요!
`uvm_info("RUN", "나의 첫 UVM! 이름: [여러분의 이름]", UVM_MEDIUM)
```

**확인 사항**: 출력 로그에서 수정한 메시지가 잘 나오는지 확인합니다.

**[실습 1-3] 페이즈(Phase) 실행 순서 확인하기**

`hello_test` 클래스의 `build_phase` 뒤에 아래 코드를 추가하고 실행 순서를 확인하세요:

```systemverilog
// build_phase 뒤에 아래 코드를 추가해보세요!

virtual function void connect_phase(uvm_phase phase);
  super.connect_phase(phase);
  `uvm_info("CONNECT", "connect_phase가 실행되었습니다!", UVM_MEDIUM)
endfunction

virtual function void end_of_elaboration_phase(uvm_phase phase);
  super.end_of_elaboration_phase(phase);
  `uvm_info("EOE", "end_of_elaboration_phase가 실행되었습니다!", UVM_MEDIUM)
endfunction

virtual function void start_of_simulation_phase(uvm_phase phase);
  super.start_of_simulation_phase(phase);
  `uvm_info("SOS", "start_of_simulation_phase가 실행되었습니다!", UVM_MEDIUM)
endfunction

virtual function void extract_phase(uvm_phase phase);
  super.extract_phase(phase);
  `uvm_info("EXTRACT", "extract_phase가 실행되었습니다!", UVM_MEDIUM)
endfunction

virtual function void check_phase(uvm_phase phase);
  super.check_phase(phase);
  `uvm_info("CHECK", "check_phase가 실행되었습니다!", UVM_MEDIUM)
endfunction

virtual function void final_phase(uvm_phase phase);
  super.final_phase(phase);
  `uvm_info("FINAL", "final_phase가 실행되었습니다!", UVM_MEDIUM)
endfunction
```

**예상 실행 순서**:

```
build --> connect --> end_of_elaboration --> start_of_simulation
  --> run --> extract --> check --> report --> final
```

> **확인 포인트**: 출력 로그에서 각 페이즈(Phase)가 위 순서대로 실행되는지 확인하세요. 이 순서는 UVM이 보장하므로 절대 바뀌지 않습니다.

<details>
<summary>[실습 1-3] 완성 코드 (클릭하여 펼치기) -- 코드 합치기가 어려우면 이 코드를 그대로 복사하세요</summary>

```systemverilog
`include "uvm_macros.svh"
import uvm_pkg::*;

class hello_test extends uvm_test;
  `uvm_component_utils(hello_test)

  function new(string name = "hello_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    `uvm_info("BUILD", "build_phase가 실행되었습니다!", UVM_MEDIUM)
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    `uvm_info("CONNECT", "connect_phase가 실행되었습니다!", UVM_MEDIUM)
  endfunction

  virtual function void end_of_elaboration_phase(uvm_phase phase);
    super.end_of_elaboration_phase(phase);
    `uvm_info("EOE", "end_of_elaboration_phase가 실행되었습니다!", UVM_MEDIUM)
  endfunction

  virtual function void start_of_simulation_phase(uvm_phase phase);
    super.start_of_simulation_phase(phase);
    `uvm_info("SOS", "start_of_simulation_phase가 실행되었습니다!", UVM_MEDIUM)
  endfunction

  virtual task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    `uvm_info("RUN", "run_phase가 실행되었습니다!", UVM_MEDIUM)
    #100;
    phase.drop_objection(this);
  endtask

  virtual function void extract_phase(uvm_phase phase);
    super.extract_phase(phase);
    `uvm_info("EXTRACT", "extract_phase가 실행되었습니다!", UVM_MEDIUM)
  endfunction

  virtual function void check_phase(uvm_phase phase);
    super.check_phase(phase);
    `uvm_info("CHECK", "check_phase가 실행되었습니다!", UVM_MEDIUM)
  endfunction

  virtual function void report_phase(uvm_phase phase);
    `uvm_info("REPORT", "report_phase가 실행되었습니다!", UVM_MEDIUM)
  endfunction

  virtual function void final_phase(uvm_phase phase);
    super.final_phase(phase);
    `uvm_info("FINAL", "final_phase가 실행되었습니다!", UVM_MEDIUM)
  endfunction

endclass

module top;
  initial begin
    run_test("hello_test");
  end
endmodule
```

</details>

### 1.4.5 예제 심화: 간단한 트랜잭션(Transaction) 맛보기

지금까지 UVM의 기본 구조를 익혔습니다. 이제 UVM의 가장 핵심 개념 중 하나인 **트랜잭션(Transaction)**을 살짝 맛봅시다.

> **트랜잭션(Transaction)이란?**
> 검증에서 컴포넌트 간에 주고받는 **데이터 묶음**입니다. 예를 들어, "주소 0x10에 데이터 0xFF를 쓰기" 같은 하나의 동작 단위를 하나의 트랜잭션으로 표현합니다.

**[예제 1-2] simple_transaction.sv**

```systemverilog
// ============================================
// 예제 1-2: 간단한 트랜잭션(Transaction)
// 목적: UVM에서 데이터가 어떻게 표현되는지 이해
// 파일: simple_transaction.sv
// ============================================

`include "uvm_macros.svh"
import uvm_pkg::*;

// ----------------------------------------
// 트랜잭션(Transaction) 클래스
// - 검증에서 주고받는 "데이터 묶음"
// - uvm_sequence_item을 상속
//
// 참고: uvm_sequence_item은 uvm_object 계열입니다.
//   - uvm_component: 계층 구조가 있는 컴포넌트 (test, env, agent 등)
//   - uvm_object: 데이터 객체 (transaction, sequence 등)
// ----------------------------------------
class simple_packet extends uvm_sequence_item;

  // 랜덤(rand) 변수: UVM이 자동으로 값을 생성해줌!
  rand bit [7:0]  addr;     // 주소 (0~255 범위에서 랜덤)
  rand bit [31:0] data;     // 데이터 (32비트 랜덤)
  rand bit        write;    // 읽기/쓰기 (0 또는 1 랜덤)

  // 제약 조건(Constraint): 랜덤이지만 규칙은 있어야 함
  constraint addr_range_c {
    addr inside {[8'h00 : 8'h7F]};  // 하위 절반 주소 범위만 사용 (0~127)
  }

  constraint data_align_c {
    data % 4 == 0;  // 4바이트 정렬된 데이터만 생성
  }

  // 팩토리(Factory) 등록
  // 참고: sequence_item은 uvm_object_utils를 사용합니다!
  //       (uvm_component_utils가 아님)
  `uvm_object_utils_begin(simple_packet)
    `uvm_field_int(addr,  UVM_ALL_ON)  // 자동 출력/비교/복사 지원
    `uvm_field_int(data,  UVM_ALL_ON)
    `uvm_field_int(write, UVM_ALL_ON)
  `uvm_object_utils_end

  // 생성자
  function new(string name = "simple_packet");
    super.new(name);
  endfunction

endclass

// ----------------------------------------
// 테스트(Test): 트랜잭션 생성 및 출력
// ----------------------------------------
class transaction_test extends uvm_test;
  `uvm_component_utils(transaction_test)

  function new(string name = "transaction_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  // build_phase는 이 예제에서 할 일이 없으므로 생략합니다.
  // (예제 1-1에서 보았듯이, 필요한 경우에만 구현하면 됩니다.)

  virtual task run_phase(uvm_phase phase);
    simple_packet pkt;  // 트랜잭션 변수 선언

    phase.raise_objection(this);

    `uvm_info("TEST", "=== 트랜잭션(Transaction) 생성 테스트 ===", UVM_MEDIUM)

    // 5개의 랜덤 패킷 생성
    // 참고: uvm_object 계열(transaction 등)은 run_phase에서 create 가능하지만,
    //       uvm_component 계열(env, agent 등)은 반드시 build_phase에서 create해야 합니다.
    repeat(5) begin
      // create: UVM 팩토리(Factory)를 통한 객체 생성
      pkt = simple_packet::type_id::create("pkt");

      // randomize: 제약 조건(Constraint) 내에서 랜덤 값 생성
      if (!pkt.randomize())
        `uvm_fatal("TEST", "랜덤화 실패!")

      // 패킷 내용 출력
      `uvm_info("TEST", $sformatf("패킷 생성: addr=0x%02h, data=0x%08h, %s",
                pkt.addr, pkt.data, pkt.write ? "WRITE" : "READ"), UVM_MEDIUM)
    end

    `uvm_info("TEST", "=== 테스트 완료 ===", UVM_MEDIUM)

    phase.drop_objection(this);
  endtask

endclass

// ----------------------------------------
// 최상위 모듈
// ----------------------------------------
module top;
  initial begin
    run_test("transaction_test");
  end
endmodule
```

> **실무 참고**: `uvm_field_*` 매크로는 학습용으로 편리하지만, 시뮬레이션 성능을 크게 저하시킬 수 있습니다 (10배 이상 느려지는 경우도 있음). 실무 프로젝트에서는 `do_copy()`, `do_compare()`, `do_print()` 메서드를 직접 구현하는 것이 일반적입니다. 이에 대해서는 Chapter 6에서 자세히 다룹니다.

**실행 결과 (예시 - 랜덤이므로 매번 다름)**:

```
UVM_INFO @ 0: uvm_test_top [TEST] === 트랜잭션(Transaction) 생성 테스트 ===
UVM_INFO @ 0: uvm_test_top [TEST] 패킷 생성: addr=0x3a, data=0x00001f2c, WRITE
UVM_INFO @ 0: uvm_test_top [TEST] 패킷 생성: addr=0x17, data=0x0000a8b0, READ
UVM_INFO @ 0: uvm_test_top [TEST] 패킷 생성: addr=0x05, data=0x00004d64, WRITE
UVM_INFO @ 0: uvm_test_top [TEST] 패킷 생성: addr=0x51, data=0x0000c3f8, READ
UVM_INFO @ 0: uvm_test_top [TEST] 패킷 생성: addr=0x42, data=0x00000210, WRITE
UVM_INFO @ 0: uvm_test_top [TEST] === 테스트 완료 ===
```

> **결과 확인**: addr 값이 모두 0x00~0x7F 범위 이내인지, data 값이 모두 4의 배수인지 확인해 보세요. 제약 조건(Constraint)이 제대로 적용된 것입니다!

**핵심 포인트**:

| 개념 | 설명 |
|------|------|
| `rand` 키워드 | 변수 앞에 붙이면 UVM이 자동으로 랜덤 값을 생성 |
| `constraint` | "의미 있는 랜덤" 값을 만들기 위한 규칙 정의 |
| `type_id::create` | UVM 팩토리(Factory)를 통한 표준 객체 생성 방식 (`new()` 대신 사용 -- 나중에 객체를 유연하게 교체할 수 있게 해줌. Chapter 4에서 자세히 설명) |
| `randomize()` | 제약 조건 내에서 랜덤 값을 실제로 생성하는 함수 |

> **전통적 방식과 비교**: 수동으로 테스트 값을 일일이 넣을 필요 없이, **자동으로 다양한 경우를 테스트**할 수 있습니다. 이것이 바로 UVM의 "제약 기반 랜덤 검증(Constrained Random Verification)"의 핵심입니다!

**[실습 1-4] 트랜잭션 수정해보기**

아래 사항을 직접 수정하고 실행해 보세요:

1. `repeat(5)`를 `repeat(10)`으로 바꿔서 패킷 10개를 생성해 보세요.
2. `data_align_c` 제약 조건을 `data % 8 == 0`으로 바꿔보세요 (8바이트 정렬).
3. 새로운 제약 조건을 추가해 보세요: `constraint write_bias_c { write dist {1 := 3, 0 := 1}; }`

> **`dist` 문법 설명**: `dist`는 distribution(분포)의 약자입니다. `write dist {1 := 3, 0 := 1}`는 "write가 1(WRITE)이 될 확률 가중치 3, 0(READ)이 될 확률 가중치 1"을 의미합니다. 즉, **쓰기가 약 75%, 읽기가 약 25%** 비율로 생성됩니다. 10개 패킷을 생성하면 대략 7~8개가 WRITE일 것입니다.

> **확인 포인트**: 제약 조건을 바꿀 때마다 출력 결과가 어떻게 달라지는지 관찰해 보세요.

---

## 1.5 Chapter 1 정리

### 핵심 요약

| 번호 | 내용 | 키워드 |
|------|------|--------|
| 1 | UVM은 표준화된 검증 방법론이다 | IEEE 1800.2, Accellera |
| 2 | 재사용성과 자동화가 핵심 장점이다 | 팩토리(Factory), 랜덤 검증 |
| 3 | UVM 테스트벤치(Testbench)는 계층 구조를 갖는다 | 테스트 -> 환경 -> 에이전트 -> 드라이버/모니터 |
| 4 | 페이즈(Phase) 순서대로 자동 실행된다 | build -> connect -> ... -> run -> ... -> report -> final (총 9개) |
| 5 | 트랜잭션(Transaction) = 검증 데이터 묶음 | uvm_sequence_item, rand, constraint |
| 6 | EDA Playground로 무료 실습이 가능하다 | edaplayground.com |

### 용어 정리

| 한글 용어 | 영어 | 설명 |
|-----------|------|------|
| 검증 | Verification | 설계가 의도대로 동작하는지 확인하는 과정 |
| 테스트벤치 | Testbench | 검증을 위한 시뮬레이션 환경 |
| DUT | Device Under Test | 검증 대상이 되는 설계 |
| 트랜잭션 | Transaction | 검증에서 주고받는 데이터 단위 |
| 페이즈 | Phase | UVM의 실행 단계 (build, connect, run 등) |
| 팩토리 | Factory | UVM의 객체 생성/관리 시스템 |
| 오브젝션 | Objection | 시뮬레이션 종료를 제어하는 메커니즘 |
| 커버리지 | Coverage | 검증 완료 정도를 측정하는 지표 |
| 제약 조건 | Constraint | 랜덤 값의 범위/규칙을 정의하는 것 |

### 셀프 체크 (Self-Check)

이 Chapter를 마치면서 다음 질문에 답해 보세요:

1. UVM은 어떤 문제를 해결하기 위해 만들어졌나요?
2. UVM 테스트벤치(Testbench)의 주요 컴포넌트 3가지를 말해 보세요.
3. `phase.raise_objection(this)`는 왜 필요한가요?
4. `rand` 키워드와 `constraint`의 관계를 설명해 보세요.
5. UVM 페이즈(Phase) 중 시간이 소모되는(task인) 페이즈는 무엇인가요?

> **답을 바로 확인하지 말고**, 먼저 직접 생각해 보세요. 답이 떠오르지 않으면 해당 절을 다시 읽어보는 것을 추천합니다.

<details>
<summary>셀프 체크 답안 확인 (클릭하여 펼치기)</summary>

1. 전통적 검증 방식의 수동 작성, 재사용 불가, 커버리지 측정 어려움, 팀 협업 어려움 문제를 해결하기 위해 만들어졌습니다.
2. 테스트(Test), 환경(Environment), 에이전트(Agent) (또는 드라이버, 모니터, 스코어보드 등)
3. 오브젝션(Objection)이 없으면 `run_phase`가 시작되자마자 시뮬레이션이 종료됩니다. raise_objection으로 "아직 끝내지 마세요"라고 알려야 테스트가 진행됩니다.
4. `rand`는 변수를 랜덤으로 생성하겠다는 선언이고, `constraint`는 그 랜덤 값이 지켜야 할 규칙/범위를 정의합니다. 둘을 함께 사용하면 "의미 있는 랜덤 값"을 생성할 수 있습니다.
5. `run_phase`입니다. `run_phase`만 `task`로 선언되며, `#delay` 등 시뮬레이션 시간 소모가 가능합니다.

</details>

### 다음 Chapter 미리보기

**Chapter 2: 환경 설정**에서는 다음 내용을 학습합니다:
- 로컬 시뮬레이션 환경 상세 설정
- 프로젝트 디렉토리 구조 설계
- 컴파일 & 실행 자동화 (Makefile 심화)
- 디버깅 도구 소개 (DVE, Verdi)

---

> **저자 노트**: 이 Chapter에서는 UVM의 큰 그림을 먼저 잡았습니다. "세부 내용이 이해 안 돼도 괜찮습니다." 앞으로 각 컴포넌트를 하나씩 깊이 있게 배울 것입니다. 지금은 "UVM은 이런 거구나!"라는 감을 잡는 것이 목표입니다.
