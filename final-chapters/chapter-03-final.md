# Chapter 3: SystemVerilog 핵심

> **학습 목표**
> - SystemVerilog의 클래스(Class)와 객체(Object)의 개념을 이해한다
> - 상속(Inheritance)과 다형성(Polymorphism)을 활용할 수 있다
> - SystemVerilog 인터페이스(Interface)의 역할과 기본 사용법을 익힌다
> - 랜덤화(Randomization)와 제약 조건(Constraint)으로 테스트 데이터를 생성할 수 있다
> - 열거형(Enum), 구조체(Struct), 타입 정의(Typedef)를 활용할 수 있다

> **학습 가이드**: 이 챕터는 내용이 많습니다. 한 번에 다 읽으려 하지 말고 **두 번에 나눠 학습**하는 것을 추천합니다:
> - **1일차**: 3.1~3.3 (클래스, 상속, 다형성) — OOP의 핵심
> - **2일차**: 3.4~3.6 (인터페이스, 랜덤화, 기타 타입) — 검증 도구

---

## 3.1 왜 SystemVerilog를 배워야 하는가?

> **이 절의 목표**: Verilog와 SystemVerilog의 차이를 이해하고, UVM에 SystemVerilog가 필요한 이유를 납득합니다.

### 3.1.1 Verilog의 한계

Chapter 1에서 UVM은 **객체지향(OOP, Object-Oriented Programming)** 기반이라고 배웠습니다. 그런데 기존 Verilog에는 클래스(Class)가 없습니다:

| 기능 | Verilog (1995/2001) | SystemVerilog (2005/2012) |
|------|-------------------|--------------------------|
| 기본 구조 | module, always, assign | Verilog 전체 + 아래 확장 |
| 객체지향 | 없음 | 클래스, 상속, 다형성 |
| 검증 자동화 | 없음 | 랜덤화, 제약 조건 |
| 신호 관리 | 개별 wire/reg | 인터페이스, 어서션 |
| 재사용성 | 낮음 (module 복사) | 높음 (상속, 확장) |

> **핵심**: SystemVerilog = Verilog + **검증을 위한 확장 기능**. UVM은 이 확장 기능 위에 만들어져 있으므로, SystemVerilog 기초를 먼저 배워야 합니다.

### 3.1.2 이 챕터에서 배울 것

UVM에서 가장 많이 쓰는 SystemVerilog 기능만 골라서 배웁니다:

| 기능 | UVM에서의 용도 | 배울 절 |
|------|--------------|--------|
| 클래스(Class) & 객체(Object) | 모든 UVM 컴포넌트의 기반 | 3.2 |
| 상속(Inheritance) & 다형성(Polymorphism) | `uvm_test`, `uvm_driver` 등 확장 | 3.3 |
| 인터페이스(Interface) | DUT와 테스트벤치 연결 | 3.4 |
| 랜덤화(Randomization) & 제약 조건(Constraint) | 테스트 데이터 자동 생성 | 3.5 |
| 열거형(Enum), 구조체(Struct), 타입 정의(Typedef) | 가독성 높은 코드 작성 | 3.6 |

> **범위 안내**: 이 챕터는 "UVM을 위한 SystemVerilog"입니다. SystemVerilog의 모든 문법을 다루지 않고, UVM에서 실제로 사용하는 핵심만 집중합니다.

> **실습 환경**: Chapter 2에서 설정한 EDA Playground에서 `testbench.sv`에 코드를 복사하여 실행하세요. 시뮬레이터 설정(SystemVerilog, UVM 1.2)은 Chapter 2와 동일합니다.

이제 첫 번째이자 가장 중요한 개념인 클래스를 알아봅시다.

---

## 3.2 클래스(Class)와 객체(Object)

> **이 절의 목표**: 클래스와 객체의 관계를 이해하고, SystemVerilog에서 클래스를 정의하고 사용할 수 있게 됩니다.

### 3.2.1 module과 class의 차이

Verilog에서는 모든 것을 `module`로 만들었습니다. SystemVerilog에서는 검증용 코드를 `class`로 만듭니다:

| 비교 | `module` | `class` |
|------|----------|---------|
| 용도 | **하드웨어 설계** (DUT) | **검증 코드** (테스트벤치) |
| 인스턴스 생성 | 컴파일 시 고정 | **실행 중** 동적 생성 가능 |
| 상속 | 불가능 | **가능** (extends) |
| 메모리 | 정적 할당 | **동적 할당** (new) |
| UVM에서 | DUT 작성에만 사용 | **모든 UVM 컴포넌트**에 사용 |

> **기억하세요**: 하드웨어 = module, 검증 = class. UVM에서 작성하는 코드는 대부분 class입니다.

### 3.2.2 첫 번째 클래스 만들기

C++의 class와 매우 비슷합니다. C++ 경험이 있다면 금방 익숙해질 것입니다:

**[예제 3-1] 간단한 패킷 클래스**

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 3-1] 간단한 패킷 클래스
// 목적: class 정의, new(), 멤버 변수/함수 사용법 이해

module top;

  // ── 클래스 정의 ──
  // C++: class Packet { ... };
  // SV:  class packet; ... endclass
  class packet;
    // 멤버 변수 (C++의 멤버 변수와 동일)
    bit [7:0]  addr;    // 주소
    bit [31:0] data;    // 데이터
    bit        write;   // 1: 쓰기, 0: 읽기

    // 생성자 (C++의 constructor와 동일)
    function new(bit [7:0] addr, bit [31:0] data, bit write);
      this.addr  = addr;    // this: 자기 자신을 가리킴 (C++과 동일)
      this.data  = data;
      this.write = write;
    endfunction

    // 멤버 함수 (C++의 메서드와 동일)
    function void display();
      $display("  Packet: addr=0x%02h, data=0x%08h, %s",
               addr, data, write ? "WRITE" : "READ");
    endfunction
  endclass

  // ── 객체 생성 및 사용 ──
  initial begin
    packet pkt1, pkt2;  // 변수 선언 (아직 객체가 아님 — null 상태)

    // new()로 객체 생성 (C++과 동일)
    pkt1 = new(8'h10, 32'hDEAD_BEEF, 1);  // 쓰기 패킷
    pkt2 = new(8'h20, 32'hCAFE_0000, 0);  // 읽기 패킷

    $display("=== 패킷 출력 ===");
    pkt1.display();  // 메서드 호출 (C++의 pkt1.display()와 동일)
    pkt2.display();
  end
endmodule
```

**예상 출력**:
```
=== 패킷 출력 ===
  Packet: addr=0x10, data=0xdeadbeef, WRITE
  Packet: addr=0x20, data=0xcafe0000, READ
```

> **참고**: 예상 출력의 세부 형식(대소문자, 줄 번호 등)은 시뮬레이터에 따라 다를 수 있습니다. 핵심 내용이 같으면 정상입니다.

> **C++ 경험자를 위한 비교**:
>
> | C++ | SystemVerilog | 비고 |
> |-----|-------------|------|
> | `class Packet { };` | `class packet; endclass` | 세미콜론 위치 다름 |
> | `Packet* pkt = new Packet();` | `pkt = new();` | SV는 포인터 개념 없이 자동 관리 |
> | `delete pkt;` | 불필요 | SV는 사용하지 않는 객체를 자동으로 정리합니다(가비지 컬렉션, Garbage Collection) |
> | `pkt->display()` | `pkt.display()` | SV는 항상 `.` 사용 |

> **참고**: SystemVerilog의 class 멤버 변수는 기본적으로 **public**(외부에서 접근 가능)입니다. C++이나 Java의 private 기본값과 다르니 주의하세요. `local`(private에 해당)과 `protected` 키워드도 있지만, UVM 학습 단계에서는 기본값(public)만 사용합니다.

### 3.2.3 클래스 vs 객체: 붕어빵 비유

```
클래스 (Class)  =  붕어빵 틀        → 설계도 (하나만 있으면 됨)
객체 (Object)   =  실제 붕어빵       → 설계도로 찍어낸 실물 (여러 개 가능)

packet pkt1 = new(...);   // 붕어빵 1개 만듦
packet pkt2 = new(...);   // 붕어빵 또 1개 만듦
                           // 각각 다른 맛(데이터)을 가질 수 있음!
```

```
┌───────────────────┐
│  class packet     │  ← 클래스 (설계도)
│  ┌─────────────┐  │
│  │ addr, data  │  │
│  │ write       │  │
│  │ display()   │  │
│  └─────────────┘  │
└─────────┬─────────┘
          │ new()
    ┌─────┴─────┐
    ▼           ▼
┌────────┐ ┌────────┐
│ pkt1   │ │ pkt2   │  ← 객체 (실체)
│ 0x10   │ │ 0x20   │    각각 다른 데이터를 가짐
│ WRITE  │ │ READ   │
└────────┘ └────────┘
```

> **UVM과의 연결**: Chapter 1에서 본 `class hello_test extends uvm_test`에서 `hello_test`가 클래스이고, `run_test("hello_test")`가 호출될 때 UVM이 내부적으로 `new()`를 호출하여 객체를 만듭니다.

### 3.2.4 핸들(Handle) — 클래스 변수의 정체

클래스 변수는 객체 자체가 아니라 객체를 **가리키는 핸들(참조)**입니다. C++의 포인터와 비슷하지만, SystemVerilog에서는 포인터 연산이 없어 더 안전합니다:

```systemverilog
packet pkt1 = new(8'h10, 32'h1111, 1);  // 객체 A 생성, pkt1이 가리킴
packet pkt2;

pkt2 = pkt1;  // ⚠️ 객체가 복사되는 게 아닙니다!
              // pkt2도 같은 객체 A를 가리키게 됩니다

pkt1.addr = 8'hFF;      // pkt1을 통해 addr 변경
$display(pkt2.addr);    // 0xFF가 출력됨! pkt2도 같은 객체를 보고 있으니까
```

```
pkt2 = pkt1; 실행 후:

pkt1 ──┐
       ├──→ [ 객체 A (addr=0xFF) ]   ← 하나의 객체를 둘이 공유
pkt2 ──┘
```

> **주의**: `pkt2 = pkt1;`은 객체를 복사하는 것이 아니라, **같은 객체를 가리키는 핸들(참조)을 복사**합니다. pkt1의 데이터를 바꾸면 pkt2로 접근해도 바뀐 값이 보입니다. 객체를 독립적으로 복사하려면 Chapter 6에서 배울 `copy()` 메서드가 필요합니다.

### 3.2.5 null 참조 에러 — 가장 흔한 실수

```systemverilog
packet pkt;        // 선언만 함 → null 상태 (아무 객체도 가리키지 않음)
pkt.display();     // 에러! null 핸들의 메서드를 호출하려고 함
```

```
** Fatal: (SIGSEGV) Bad handle or reference.
```

**해결**: 반드시 `pkt = new(...);`로 객체를 생성한 후 사용하세요. UVM에서는 `type_id::create()`로 생성합니다.

> **실무 참고**: 이 챕터의 예제에서는 편의상 `module` 안에 class를 정의했지만, 실무와 UVM에서는 class를 `package` 안에 정의하고 `import`하여 사용합니다. 이 방식은 Chapter 5에서 실제 프로젝트를 구성할 때 배웁니다.

클래스의 기본을 익혔으니, 이제 클래스의 진정한 힘인 상속을 배워봅시다.

---

## 3.3 상속(Inheritance)과 다형성(Polymorphism)

> **이 절의 목표**: extends로 클래스를 확장하고, virtual 함수를 통한 다형성을 이해합니다.

### 3.3.1 상속이란?

기존 클래스를 **확장(extends)**하여 새 클래스를 만드는 것입니다. UVM의 모든 컴포넌트가 이 방식으로 만들어집니다:

```
uvm_object
  └─ uvm_component
       ├─ uvm_test            ← Chapter 1-2에서 사용한 것
       ├─ uvm_env
       ├─ uvm_agent
       ├─ uvm_driver
       └─ uvm_monitor
```

> **비유**: 상속 = "기본 기능을 물려받고, 나만의 기능을 추가하는 것". 스마트폰을 생각해보세요 — 기본 전화 기능(부모)은 그대로 가지면서, 각 앱(자식)은 자기만의 기능을 추가합니다.

### 3.3.2 상속 실습

**[예제 3-2] 상속으로 클래스 확장하기**

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 3-2] 상속(Inheritance) 실습
// 목적: extends, super, 메서드 오버라이드 이해

module top;

  // ── 부모 클래스: 기본 패킷 ──
  class base_packet;
    bit [7:0]  addr;
    bit [31:0] data;

    function new(bit [7:0] addr, bit [31:0] data);
      this.addr = addr;
      this.data = data;
    endfunction

    // virtual: 자식 클래스에서 재정의(오버라이드)할 수 있게 허용
    virtual function void display();
      $display("  [Base] addr=0x%02h, data=0x%08h", addr, data);
    endfunction

    virtual function int get_size();
      return 5;  // 기본 크기: addr(1) + data(4) = 5바이트
    endfunction
  endclass

  // ── 자식 클래스: 확장 패킷 ──
  // base_packet의 모든 기능을 물려받고, 추가 기능을 넣습니다
  class extended_packet extends base_packet;
    bit [15:0] checksum;  // 추가 필드: 체크섬

    function new(bit [7:0] addr, bit [31:0] data, bit [15:0] checksum);
      super.new(addr, data);     // 부모 생성자 호출 (필수!)
      this.checksum = checksum;
    endfunction

    // 부모의 display()를 재정의 (오버라이드)
    virtual function void display();
      $display("  [Extended] addr=0x%02h, data=0x%08h, checksum=0x%04h",
               addr, data, checksum);
    endfunction

    // 부모의 get_size()를 재정의
    virtual function int get_size();
      return super.get_size() + 2;  // 부모 크기 + checksum(2바이트)
    endfunction
  endclass

  initial begin
    base_packet     bp;
    extended_packet ep;

    bp = new(8'hAA, 32'h1111_2222);
    ep = new(8'hBB, 32'h3333_4444, 16'hFF00);

    $display("=== 기본 패킷 ===");
    bp.display();
    $display("  크기: %0d 바이트", bp.get_size());

    $display("=== 확장 패킷 ===");
    ep.display();
    $display("  크기: %0d 바이트", ep.get_size());
  end
endmodule
```

**예상 출력**:
```
=== 기본 패킷 ===
  [Base] addr=0xaa, data=0x11112222
  크기: 5 바이트
=== 확장 패킷 ===
  [Extended] addr=0xbb, data=0x33334444, checksum=0xff00
  크기: 7 바이트
```

**핵심 키워드 정리**:

| 키워드 | 의미 | C++ 대응 | UVM에서의 사용 |
|--------|------|----------|---------------|
| `extends` | 부모 클래스를 상속 | `:` (콜론) | `class my_test extends uvm_test` |
| `super` | 부모 클래스 참조 | 부모 클래스명 명시 | `super.new(name, parent)`, `super.build_phase(phase)` |
| `virtual` | 자식이 재정의할 수 있게 허용 | `virtual` (동일) | 모든 페이즈 함수에 사용 |
| `this` | 자기 자신 참조 | `this` (동일) | `phase.raise_objection(this)` |

### 3.3.3 다형성(Polymorphism) — 왜 virtual이 중요한가?

다형성이란 **같은 명령을 내려도 객체마다 다르게 반응하는 것**입니다. "소리 내!"라고 하면 강아지는 멍멍, 고양이는 야옹이라고 합니다. 코드로 표현하면, **부모 타입 변수에 자식 객체를 담아도 자식의 함수가 호출되는 것**입니다:

**[예제 3-3] 다형성 체험**

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 3-3] 다형성(Polymorphism) 체험
// 목적: virtual 함수의 동작 원리 이해

module top;

  class animal;
    string name;
    function new(string name);
      this.name = name;
    endfunction

    // virtual이 있으면: 실제 객체 타입의 함수가 호출됨
    virtual function void speak();
      $display("  %s: ...(소리 없음)", name);
    endfunction
  endclass

  class dog extends animal;
    function new(string name);
      super.new(name);
    endfunction
    virtual function void speak();
      $display("  %s: 멍멍!", name);
    endfunction
  endclass

  class cat extends animal;
    function new(string name);
      super.new(name);
    endfunction
    virtual function void speak();
      $display("  %s: 야옹!", name);
    endfunction
  endclass

  initial begin
    // 부모 타입 변수에 자식 객체를 담을 수 있음!
    animal animals[3];

    // 자식 객체를 만들어서 부모 타입 배열에 저장
    dog   d;
    cat   c;

    animals[0] = new("동물");          // animal 객체
    d = new("강아지");
    c = new("고양이");
    animals[1] = d;                    // dog 객체를 animal 변수에 저장
    animals[2] = c;                    // cat 객체를 animal 변수에 저장

    $display("=== 다형성 데모 ===");
    foreach (animals[i])
      animals[i].speak();  // 각 객체의 실제 타입에 맞는 함수가 호출됨!
  end
endmodule
```

**예상 출력**:
```
=== 다형성 데모 ===
  동물: ...(소리 없음)
  강아지: 멍멍!
  고양이: 야옹!
```

다형성의 동작 원리를 그림으로 보면:

```
animal animals[3]
  [0] ──→ animal 객체    → speak() → "...(소리 없음)"
  [1] ──→ dog 객체       → speak() → "멍멍!"        ← virtual 덕분!
  [2] ──→ cat 객체       → speak() → "야옹!"        ← virtual 덕분!

모두 animal 타입 변수이지만, 실제 객체에 맞는 함수가 호출됩니다.
```

> **UVM과의 연결**: UVM은 내부적으로 `uvm_component` 타입의 배열에 다양한 자식 객체(test, env, driver 등)를 저장합니다. `virtual`이 있기 때문에 각 컴포넌트의 `build_phase()`, `run_phase()` 등이 올바르게 호출됩니다. Chapter 1-2에서 `virtual task run_phase`로 선언한 이유가 바로 이것입니다.

### 3.3.4 virtual 없이 실행하면?

`virtual`을 빼면 **부모의 함수**가 호출됩니다:

```systemverilog
// virtual 없는 경우
function void speak();  // virtual 키워드 없음
  $display("  %s: ...", name);
endfunction
```

```
결과:
  동물: ...
  강아지: ...    ← 멍멍! 대신 부모의 함수가 호출됨
  고양이: ...    ← 야옹! 대신 부모의 함수가 호출됨
```

> **결론**: UVM에서 모든 페이즈 함수에 `virtual`을 붙이는 이유는, 부모(uvm_test)가 아니라 **우리가 작성한 자식 클래스의 함수**가 호출되도록 하기 위해서입니다.

> **미리보기**: 부모 타입 변수에서 자식 타입의 고유 멤버에 접근하려면 `$cast`라는 형변환(타입 캐스팅)이 필요합니다. 이는 Chapter 6에서 시퀀스를 다룰 때 배웁니다.

상속과 다형성을 이해했으니, 이제 하드웨어와 검증 코드를 연결하는 인터페이스를 배워봅시다.

---

## 3.4 인터페이스(Interface)

> **이 절의 목표**: SystemVerilog 인터페이스의 역할을 이해하고, 신호를 묶어서 관리하는 방법을 익힙니다.

### 3.4.1 인터페이스가 필요한 이유

DUT(설계)와 테스트벤치를 연결할 때, 신호를 하나하나 연결하면 번거롭습니다:

```
전통적 방식 (Verilog):          인터페이스 방식 (SystemVerilog):
  wire clk, reset, valid;        simple_if bus_if(clk);
  wire ready;                    // 관련 신호를 하나로 묶기!
  wire [7:0] addr;
  wire [31:0] data;
  // 신호가 늘어나면 관리 불가!
```

> **비유**: 인터페이스 = **멀티탭**. 전원 코드 10개를 하나하나 벽에 꽂는 대신, 멀티탭 하나에 모아서 관리하는 것과 같습니다.

인터페이스가 DUT와 테스트벤치 사이에서 어떤 역할을 하는지 그림으로 봅시다:

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   테스트벤치       │    │   인터페이스       │    │      DUT         │
│   (class 기반)    │◀──▶│   (interface)     │◀──▶│   (module)       │
│                  │ 신호│  addr, data,     │ 신호│   simple_dut     │
│   드라이버/모니터  │ 접근│  valid, ready    │ 연결│                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

### 3.4.2 인터페이스 정의와 사용

예제 코드가 길어서, 3개 부분으로 나누어 설명합니다.

**[예제 3-4a] 인터페이스 정의**

먼저 관련 신호들을 하나로 묶는 인터페이스를 정의합니다:

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 3-4] SystemVerilog 인터페이스
// 목적: 인터페이스로 신호를 묶어서 관리하는 방법 이해

// ── 인터페이스 정의 ──
// 관련된 신호들을 하나로 묶습니다
interface simple_if(input logic clk);
  logic       reset;
  logic       valid;
  logic       ready;
  logic [7:0] addr;
  logic [31:0] data;

  // clocking block: 신호의 타이밍 규칙을 정의하는 블록입니다.
  // 드라이버(신호를 보내는 역할)는 output이 많고,
  // 모니터(신호를 관찰하는 역할)는 input만 있습니다.
  // 지금은 "이런 게 있다" 정도로 알아두세요.
  // Chapter 7에서 드라이버와 모니터를 구현할 때 자세히 배웁니다.
  clocking driver_cb @(posedge clk);
    output reset, valid, addr, data;
    input  ready;
  endclocking

  clocking monitor_cb @(posedge clk);
    input reset, valid, ready, addr, data;
  endclocking
endinterface
```

> **참고**: 위에서 `clocking block`을 정의했지만, 아래의 테스트벤치에서는 직접 신호를 구동합니다. clocking block을 통한 신호 구동(`bus_if.driver_cb.valid <= 1;`)은 UVM 드라이버에서 주로 사용하며, Chapter 7에서 자세히 다룹니다. 지금은 clocking block의 **존재**를 알아두는 것으로 충분합니다.

**[예제 3-4b] 간단한 DUT**

인터페이스와 연결할 간단한 DUT입니다. DUT 코드 자체를 외울 필요는 없습니다 — 인터페이스가 어떻게 연결되는지에 집중하세요:

```systemverilog
// ── 간단한 DUT (설계) ──
// 이 DUT의 동작: valid가 들어오면 ready를 1로 응답
module simple_dut(
  input  logic        clk,
  input  logic        reset,
  input  logic        valid,
  output logic        ready,
  input  logic [7:0]  addr,
  input  logic [31:0] data
);
  always_ff @(posedge clk) begin
    if (reset)
      ready <= 0;
    else if (valid)
      ready <= 1;
    else
      ready <= 0;
  end
endmodule
```

**[예제 3-4c] 테스트벤치 — 인터페이스를 통한 연결**

이제 인터페이스를 사용하여 DUT와 테스트벤치를 연결합니다:

```systemverilog
// ── 테스트벤치 ──
module top;
  logic clk = 0;
  always #5 clk = ~clk;  // 10ns 주기 클럭

  // 인터페이스 인스턴스 생성
  simple_if bus_if(clk);

  // DUT 연결 — 인터페이스의 신호를 꺼내서 연결
  simple_dut dut(
    .clk   (clk),
    .reset (bus_if.reset),
    .valid (bus_if.valid),
    .ready (bus_if.ready),
    .addr  (bus_if.addr),
    .data  (bus_if.data)
  );

  initial begin
    // 리셋
    bus_if.reset = 1;
    bus_if.valid = 0;
    bus_if.addr  = 0;
    bus_if.data  = 0;
    #20;

    bus_if.reset = 0;
    #10;

    // 쓰기 요청
    @(posedge clk);
    bus_if.valid = 1;
    bus_if.addr  = 8'h42;
    bus_if.data  = 32'hABCD_1234;

    @(posedge clk);
    bus_if.valid = 0;

    // ready 확인
    @(posedge clk);
    if (bus_if.ready)
      $display("SUCCESS: DUT가 ready를 응답했습니다!");
    else
      $display("FAIL: DUT가 응답하지 않았습니다.");

    #50;
    $finish;
  end
endmodule
```

> **실행 안내**: 위의 3개 코드 블록(인터페이스 + DUT + 테스트벤치)을 모두 하나의 `testbench.sv` 파일에 순서대로 복사하여 실행하세요.

**예상 출력**:
```
SUCCESS: DUT가 ready를 응답했습니다!
```

### 3.4.3 인터페이스의 핵심 요소

| 요소 | 역할 | 비유 |
|------|------|------|
| 신호 선언 (`logic`) | 관련 신호를 묶음 | 멀티탭의 각 콘센트 |
| `clocking block` | 타이밍 동기화 규칙 정의 (Chapter 7에서 상세 학습) | 신호등 (언제 읽고 쓸지 규칙) |
| 모드포트(modport) (이 예제에서는 생략) | 방향 제한 — 드라이버는 출력만, 모니터는 입력만 접근하도록 제한 (Chapter 7에서 상세 학습) | 입구/출구 구분 |

> **UVM과의 연결**: Chapter 7에서 배울 드라이버(Driver)와 모니터(Monitor)는 **가상 인터페이스(Virtual Interface)**를 통해 이 인터페이스에 접근합니다. 구체적으로, 드라이버는 이 인터페이스를 통해 DUT에 신호를 보내고, 모니터는 DUT의 응답 신호를 관찰합니다. 지금은 "인터페이스 = 신호 묶음"이라는 것만 기억하세요.

> **주의**: 이 절에서 배운 `interface`는 SystemVerilog의 하드웨어 연결용 인터페이스입니다. UVM에서 나오는 "virtual interface"는 이 인터페이스를 **클래스 안에서 참조하기 위한 기법**으로, Chapter 7에서 자세히 다룹니다.

> **실무 참고**: 실무에서는 인터페이스(`simple_if.sv`), DUT(`simple_dut.sv`), 테스트벤치(`tb_top.sv`)를 별도 파일로 분리합니다. 이 예제에서는 EDA Playground 제약상 하나의 파일에 넣었습니다.

인터페이스로 DUT와 테스트벤치의 연결 방법을 배웠습니다. 이제 UVM 검증의 핵심인 랜덤화를 알아봅시다.

---

## 3.5 랜덤화(Randomization)와 제약 조건(Constraint)

> **이 절의 목표**: rand 변수와 constraint를 사용하여 의미 있는 테스트 데이터를 자동 생성할 수 있게 됩니다.

### 3.5.1 왜 랜덤 테스트가 필요한가?

Chapter 1에서 전통적 방식의 수동 테스트가 비효율적이라고 배웠습니다. 랜덤화를 쓰면:

```
수동 테스트:  addr=0x00, 0x01, 0x02, ... (직접 100개 작성)
랜덤 테스트:  addr = random(0x00~0xFF)    (자동으로 1000개 생성!)
```

하지만 완전히 무작위로 값을 넣으면 **의미 없는 테스트**가 될 수 있습니다. 그래서 **제약 조건(Constraint)**으로 "의미 있는 범위"를 지정합니다:

```
┌───────────────────────────────────────────────┐
│         전체 가능한 값 (32비트 = 40억개)         │
│  ┌────────────────────────────────────┐       │
│  │    제약 조건으로 좁힌 범위           │       │
│  │  ┌──────────────────────────┐     │       │
│  │  │  의미 있는 테스트 데이터   │     │       │
│  │  │  addr: 0x00~0xFF        │     │       │
│  │  │  4의 배수만              │     │       │
│  │  └──────────────────────────┘     │       │
│  └────────────────────────────────────┘       │
└───────────────────────────────────────────────┘
```

> **UVM과의 연결**: UVM에서는 시퀀스(Sequence) 안에서 이 랜덤화를 활용하여 테스트 데이터를 자동 생성합니다. Chapter 6에서 시퀀스를, Chapter 9에서 실전 테스트 시나리오를 배웁니다.

### 3.5.2 rand와 constraint 기본

이 절에서 배우는 새 키워드가 많습니다. 먼저 핵심 3가지만 기억하세요:
- `rand`: "이 변수는 랜덤으로 생성하라"
- `constraint`: "이 규칙 안에서만 랜덤을 생성하라"
- `randomize()`: "지금 랜덤 값을 생성하라"

**[예제 3-5] 랜덤 패킷 생성**

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 3-5] 랜덤화(Randomization) 실습
// 목적: rand, constraint, randomize() 사용법 이해

module top;

  class rand_packet;
    // rand: 이 변수는 랜덤으로 생성됨
    rand bit [7:0]  addr;
    rand bit [31:0] data;
    rand bit        write;

    // randc: 모든 값을 한 번씩 순회하는 순환 랜덤(Cyclic Random)
    // 예: 2비트이면 0,1,2,3을 한 번씩 다 돌고 나서 다시 반복
    randc bit [1:0] priority;

    // ── 제약 조건 ──

    // 주소 범위 제한
    constraint addr_range_c {
      addr inside {[8'h00 : 8'h3F]};  // 0~63 범위만 허용
    }

    // 데이터 정렬
    constraint data_align_c {
      data % 4 == 0;  // 4바이트 정렬
    }

    // 쓰기/읽기 비율 조정
    constraint write_bias_c {
      write dist {1 := 7, 0 := 3};  // 쓰기 70%, 읽기 30%
    }

    function void display(int num);
      $display("  [%0d] addr=0x%02h, data=0x%08h, %s, priority=%0d",
               num, addr, data, write ? "WR" : "RD", priority);
    endfunction
  endclass

  initial begin
    rand_packet pkt = new();

    $display("=== 랜덤 패킷 10개 생성 ===");
    for (int i = 1; i <= 10; i++) begin
      // randomize(): 제약 조건 내에서 랜덤 값 생성
      if (!pkt.randomize())
        $display("ERROR: 랜덤화 실패!");
      pkt.display(i);
    end
  end
endmodule
```

**예상 출력 (값은 매번 다름)**:
```
=== 랜덤 패킷 10개 생성 ===
  [1] addr=0x1a, data=0x0003f2c0, WR, priority=2
  [2] addr=0x2f, data=0x00a81b04, WR, priority=0
  [3] addr=0x05, data=0x004d6438, RD, priority=3
  [4] addr=0x3c, data=0x00c3f850, WR, priority=1
  [5] addr=0x12, data=0x00000210, WR, priority=2
  ...
```

> **확인해보세요**: (1) addr가 모두 0x00~0x3F 범위인가? (2) data가 모두 4의 배수인가? (3) 쓰기가 약 70%인가? (4) priority가 0~3을 순회하는가?

### 3.5.3 중간 정리 — 랜덤화 핵심 키워드

여기까지 배운 키워드를 정리합니다:

| 키워드 | 의미 | 예시 |
|--------|------|------|
| `rand` | 매번 독립적으로 랜덤 값 생성 | `rand bit [7:0] addr;` |
| `randc` | 가능한 모든 값을 한 번씩 순회 후 반복 | `randc bit [1:0] priority;` |
| `constraint` | 랜덤 값의 범위/규칙 정의 | `constraint c { addr < 64; }` |
| `randomize()` | 제약 조건 내에서 랜덤 값 생성 (실행) | `if (!pkt.randomize()) ...` |

이 4가지가 핵심입니다. 아래에서 배울 `dist`, `inside`, `with`는 constraint를 더 세밀하게 제어하는 도구입니다.

### 3.5.4 자주 쓰는 제약 조건 패턴

| 패턴 | 코드 | 의미 |
|------|------|------|
| 범위 지정 | `addr inside {[0:63]}` | 0~63 사이 값 |
| 특정 값 제외 | `!(addr inside {0, 255})` | 0과 255 제외 |
| 비율 조정 | `write dist {1:=7, 0:=3}` | 1이 70%, 0이 30% |
| 조건부 제약 | `if (write) data > 0;` | 쓰기 시 data > 0 |
| 정렬 | `addr % 4 == 0` | 4의 배수만 허용 |
| 크기 제한 | `data < 256` | 256 미만 |

### 3.5.5 inline constraint (with절)

매번 클래스를 수정하지 않고, **호출 시점에 추가 제약 조건**을 넣을 수 있습니다:

> 위 [예제 3-5]의 `initial begin` 블록에서, `pkt.randomize()` 호출을 아래처럼 바꿔보세요:

```systemverilog
// 기존 제약 + 추가 제약
pkt.randomize() with { addr == 8'h10; };     // addr를 0x10으로 고정
pkt.randomize() with { data < 100; };         // data를 100 미만으로 추가 제한
pkt.randomize() with { write == 1; };         // 쓰기만 생성
```

> **실무 팁**: `with` 절은 테스트 시나리오마다 다른 조건을 적용할 때 매우 유용합니다. Chapter 9(테스트 시나리오)에서 실전 활용법을 배웁니다.

### 3.5.6 randomize() 실패 처리

제약 조건이 서로 모순되면 `randomize()`가 실패합니다:

```systemverilog
constraint impossible_c {
  addr > 200;      // addr > 200
  addr < 100;      // addr < 100  ← 동시에 만족 불가!
}

if (!pkt.randomize())
  $display("ERROR: 제약 조건 충돌! 랜덤화 실패");
```

> **주의**: `randomize()` 반환값을 항상 확인하세요. UVM에서는 실패 시 `` `uvm_fatal ``로 처리하는 것이 일반적입니다. 이 챕터에서는 UVM 매크로 없이 순수 SystemVerilog로 작성하므로 `if (!pkt.randomize())`로 체크합니다.

랜덤화로 테스트 데이터를 자동 생성하는 방법을 배웠습니다. 마지막으로, 코드의 가독성을 높여주는 유용한 타입들을 알아봅시다.

---

## 3.6 열거형(Enum), 구조체(Struct), 타입 정의(Typedef)

> **이 절의 목표**: enum, struct, typedef를 사용하여 가독성 높은 코드를 작성할 수 있게 됩니다.

### 3.6.1 열거형(Enum)

숫자 대신 **이름**으로 상태를 표현합니다:

**[예제 3-6a] 열거형 기본 사용**

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 3-6a] 열거형(Enum) 기본 사용
// 목적: enum 정의와 활용법 이해

module top;

  // 열거형 정의
  // _e 접미사는 enum임을 표시하는 실무 관례
  typedef enum bit [1:0] {
    CMD_READ  = 2'b00,
    CMD_WRITE = 2'b01,
    CMD_ERASE = 2'b10,
    CMD_IDLE  = 2'b11
  } cmd_type_e;

  initial begin
    cmd_type_e cmd;

    cmd = CMD_WRITE;
    // .name(): 열거형 값의 이름을 문자열로 반환하는 내장 메서드
    $display("명령어: %s (값: %0b)", cmd.name(), cmd);

    cmd = CMD_READ;
    $display("명령어: %s (값: %0b)", cmd.name(), cmd);

    // 숫자로 비교 (가독성 나쁨)
    // if (cmd == 2'b00) ...
    // 열거형으로 비교 (가독성 좋음)
    if (cmd == CMD_READ)
      $display("읽기 명령입니다!");
  end
endmodule
```

**예상 출력**:
```
명령어: CMD_WRITE (값: 01)
명령어: CMD_READ (값: 00)
읽기 명령입니다!
```

> **실무 관례**: 열거형 이름은 `_e` 접미사, 열거 값은 대문자로 작성합니다. UVM 코드에서도 이 관례를 따릅니다. UVM에서는 상태 머신의 상태, 트랜잭션의 명령 종류 등을 enum으로 표현합니다.

### 3.6.2 구조체(Struct)와 타입 정의(Typedef)

관련된 데이터를 하나로 묶습니다:

**[예제 3-6b] 구조체 기본 사용**

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 3-6b] 구조체(Struct) 기본 사용
// 목적: typedef struct 정의와 활용법 이해

module top;

  typedef enum bit [1:0] {
    CMD_READ  = 2'b00,
    CMD_WRITE = 2'b01,
    CMD_ERASE = 2'b10
  } cmd_type_e;

  // typedef로 구조체 정의
  // packed: 비트를 연속으로 배치 (하드웨어 레벨에서 하나의 벡터처럼 동작)
  // 지금은 "struct 앞에 packed를 관례적으로 붙인다" 정도로 이해하면 됩니다
  // _t 접미사는 type임을 표시하는 실무 관례
  typedef struct packed {
    bit [7:0]  addr;
    bit [31:0] data;
    cmd_type_e cmd;
  } packet_t;

  initial begin
    packet_t pkt;

    pkt.addr = 8'h42;
    pkt.data = 32'hDEAD_BEEF;
    pkt.cmd  = CMD_WRITE;

    $display("패킷: addr=0x%02h, data=0x%08h, cmd=%s",
             pkt.addr, pkt.data, pkt.cmd.name());
  end
endmodule
```

**예상 출력**:
```
패킷: addr=0x42, data=0xdeadbeef, cmd=CMD_WRITE
```

> **class vs struct**: `struct`는 단순한 데이터 묶음이고, `class`는 함수(메서드)와 상속이 가능합니다. UVM에서 컴포넌트와 트랜잭션은 `class`를 사용하고, 간단한 설정값이나 하드웨어 레벨 데이터는 `struct`를 사용합니다.

### 3.6.3 종합 실습: 모든 개념 활용

지금까지 배운 것을 한꺼번에 써봅시다. 처음에는 코드 전체를 이해하려 하지 말고, **먼저 실행해서 출력을 확인한 다음** 하나씩 분석해보세요.

**[예제 3-7] enum + constraint + 상속 종합 예제**

```systemverilog
// 파일: testbench.sv (EDA Playground)
// [예제 3-7] Chapter 3 종합 실습
// 목적: enum, class, 상속, rand, constraint를 함께 활용

module top;

  // ── 타입 정의 ──
  typedef enum bit [1:0] {
    CMD_READ  = 2'b00,
    CMD_WRITE = 2'b01,
    CMD_ERASE = 2'b10
  } cmd_type_e;

  // ── 기본 트랜잭션 클래스 ──
  class base_transaction;
    rand bit [7:0]   addr;
    rand bit [31:0]  data;
    rand cmd_type_e  cmd;

    constraint addr_range_c {
      addr inside {[0:127]};
    }

    constraint cmd_dist_c {
      cmd dist { CMD_READ := 4, CMD_WRITE := 5, CMD_ERASE := 1 };
    }

    function new();
    endfunction

    virtual function void display(string prefix = "");
      $display("  %s[Base] cmd=%s, addr=0x%02h, data=0x%08h",
               prefix, cmd.name(), addr, data);
    endfunction
  endclass

  // ── 확장 트랜잭션: 에러 주입 기능 추가 ──
  class error_transaction extends base_transaction;
    rand bit inject_error;    // 에러 주입 여부
    rand bit [3:0] error_type;  // 에러 종류

    constraint error_rate_c {
      inject_error dist { 1 := 1, 0 := 9 };  // 10% 확률로 에러 주입
    }

    constraint error_type_c {
      if (!inject_error) error_type == 0;
      if (inject_error) error_type inside {[1:5]};
    }

    function new();
      super.new();
    endfunction

    virtual function void display(string prefix = "");
      string err_str;
      // $sformatf: C의 sprintf와 동일한 기능.
      // 포맷에 맞게 문자열을 만들어서 반환합니다.
      err_str = inject_error ?
                $sformatf("ERR_TYPE=%0d", error_type) : "OK";
      $display("  %s[Error] cmd=%s, addr=0x%02h, data=0x%08h, status=%s",
               prefix, cmd.name(), addr, data, err_str);
    endfunction
  endclass

  initial begin
    // 동적 큐(Queue): C++의 vector와 비슷한 가변 크기 배열.
    // [$]로 선언하며, push_back()으로 끝에 추가, pop_front()로 앞에서 제거.
    // 크기를 미리 정하지 않아도 됩니다.
    base_transaction  base_q[$];
    error_transaction err_txn;

    $display("=== 에러 트랜잭션 10개 생성 ===");
    for (int i = 0; i < 10; i++) begin
      // ⚠️ 중요: 루프 안에서 매번 new()를 호출해야 합니다!
      err_txn = new();
      if (!err_txn.randomize())
        $display("ERROR: 랜덤화 실패!");

      err_txn.display($sformatf("[%0d] ", i));

      // 다형성: 부모 타입 큐에 자식 객체 저장 가능
      base_q.push_back(err_txn);
    end

    $display("\n=== 큐에서 다시 출력 (다형성) ===");
    foreach (base_q[i])
      base_q[i].display($sformatf("Q[%0d] ", i));
  end
endmodule
```

> **주의: 초보자가 자주 하는 실수**
> 위 코드에서 루프 안에 `err_txn = new();`가 있습니다. 만약 루프 **밖**에서 한 번만 `new()`를 호출하고, 루프 안에서 `randomize()`만 반복하면 어떻게 될까요?
>
> 3.2.4절에서 배운 핸들 개념을 떠올려보세요 — 큐에 같은 객체의 핸들(참조)만 쌓이게 되어, **마지막 randomize() 결과만 모든 항목에 반영**됩니다. 매 반복마다 `new()`로 새 객체를 만들어야 각각 독립적인 데이터를 가집니다.

**예상 출력 (값은 매번 다름)**:
```
=== 에러 트랜잭션 10개 생성 ===
  [0] [Error] cmd=CMD_WRITE, addr=0x2a, data=0x1f3c8800, status=OK
  [1] [Error] cmd=CMD_READ, addr=0x51, data=0x00a8b0c4, status=OK
  [2] [Error] cmd=CMD_WRITE, addr=0x17, data=0x4d640000, status=ERR_TYPE=3
  ...

=== 큐에서 다시 출력 (다형성) ===
  Q[0] [Error] cmd=CMD_WRITE, addr=0x2a, data=0x1f3c8800, status=OK
  ...
```

> **관찰 포인트**: (1) 큐에서 꺼낸 객체가 `[Error]`로 출력됩니다 — 다형성 덕분에 자식의 display()가 호출됨! (2) 에러 주입은 약 10%만 발생 (3) cmd 분포가 READ:WRITE:ERASE 약 4:5:1

---

## 3.7 체크포인트

### 셀프 체크

아래 질문에 답할 수 있다면 이 챕터를 충분히 이해한 것입니다:

1. SystemVerilog `class`와 Verilog `module`의 가장 큰 차이점은?

<details>
<summary>정답 확인</summary>

class는 상속(extends)이 가능하고, 실행 중 동적으로 객체를 생성(new)할 수 있습니다. module은 컴파일 시 인스턴스가 고정됩니다. UVM의 검증 코드는 class로, DUT는 module로 작성합니다.
</details>

2. `virtual` 키워드를 함수에 붙이는 이유는?

<details>
<summary>정답 확인</summary>

다형성(Polymorphism)을 위해서입니다. 부모 타입 변수에 자식 객체를 담았을 때, virtual이 있으면 자식의 함수가 호출됩니다. UVM에서 모든 페이즈 함수에 virtual을 붙이는 이유입니다.
</details>

3. `rand`와 `randc`의 차이점은?

<details>
<summary>정답 확인</summary>

rand는 매번 독립적으로 랜덤 값을 생성합니다. randc(순환 랜덤, Cyclic Random)는 가능한 모든 값을 한 번씩 순회한 후 반복합니다. 예를 들어 2비트 randc 변수는 0,1,2,3을 모두 한 번씩 생성한 후 다시 순회합니다.
</details>

4. `constraint`에서 `dist` 키워드의 역할은?

<details>
<summary>정답 확인</summary>

dist는 분포(distribution)를 지정합니다. `write dist {1:=7, 0:=3}`은 1이 될 확률 가중치 7, 0이 될 확률 가중치 3으로, 약 70% 확률로 1이 생성됩니다.
</details>

5. SystemVerilog `interface`의 역할은?

<details>
<summary>정답 확인</summary>

관련된 신호들을 하나로 묶어서 관리합니다. DUT와 테스트벤치 사이의 연결을 깔끔하게 해줍니다. 멀티탭처럼, 여러 신호를 하나의 bundle로 관리할 수 있습니다.
</details>

6. `pkt2 = pkt1;`을 실행하면 어떤 일이 발생하는가?

<details>
<summary>정답 확인</summary>

객체가 복사되는 것이 아니라, pkt2가 pkt1과 같은 객체를 가리키게 됩니다(핸들 복사). 따라서 pkt1을 통해 데이터를 바꾸면 pkt2로 접근해도 바뀐 값이 보입니다. 독립적인 복사를 하려면 copy() 메서드가 필요합니다.
</details>

### 연습문제

**[실습 3-1] 패킷 클래스 확장하기 (쉬움)** — 약 10분

[예제 3-1]의 `packet` 클래스에 `priority`(2비트) 멤버 변수를 추가하고, `display()` 함수에서 함께 출력하세요.

<details>
<summary>힌트</summary>

클래스 안에 `bit [1:0] priority;`를 추가하고, 생성자와 display 함수를 수정하면 됩니다.
</details>

<details>
<summary>모범 답안</summary>

```systemverilog
module top;
  class packet;
    bit [7:0]  addr;
    bit [31:0] data;
    bit        write;
    bit [1:0]  priority;  // 추가된 필드

    function new(bit [7:0] addr, bit [31:0] data, bit write, bit [1:0] priority);
      this.addr     = addr;
      this.data     = data;
      this.write    = write;
      this.priority = priority;
    endfunction

    function void display();
      $display("  Packet: addr=0x%02h, data=0x%08h, %s, priority=%0d",
               addr, data, write ? "WRITE" : "READ", priority);
    endfunction
  endclass

  initial begin
    packet pkt1, pkt2;
    pkt1 = new(8'h10, 32'hDEAD_BEEF, 1, 2'b11);  // 높은 우선순위
    pkt2 = new(8'h20, 32'hCAFE_0000, 0, 2'b00);  // 낮은 우선순위

    $display("=== 패킷 출력 ===");
    pkt1.display();
    pkt2.display();
  end
endmodule
```
</details>

**[실습 3-2] 버스트 패킷 만들기 (보통)** — 약 20분

`rand_packet` 클래스([예제 3-5])를 상속받아 `burst_packet` 클래스를 만드세요. `rand bit [3:0] burst_length;` (1~8 범위)와 `rand bit [1:0] burst_type;` (0: FIXED, 1: INCR, 2: WRAP)을 추가하세요.

<details>
<summary>힌트</summary>

`class burst_packet extends rand_packet;`으로 시작하고, burst_length의 제약 조건은 `burst_length inside {[1:8]};`로 작성합니다.
</details>

<details>
<summary>모범 답안</summary>

```systemverilog
// [예제 3-5]의 rand_packet 클래스 아래에 추가

class burst_packet extends rand_packet;
  rand bit [3:0] burst_length;
  rand bit [1:0] burst_type;  // 0: FIXED, 1: INCR, 2: WRAP

  constraint burst_length_c {
    burst_length inside {[1:8]};
  }

  constraint burst_type_c {
    burst_type inside {[0:2]};
  }

  function void display(int num);
    string type_str;
    case (burst_type)
      0: type_str = "FIXED";
      1: type_str = "INCR";
      2: type_str = "WRAP";
      default: type_str = "UNKNOWN";
    endcase
    $display("  [%0d] addr=0x%02h, data=0x%08h, %s, burst=%s(len=%0d)",
             num, addr, data, write ? "WR" : "RD", type_str, burst_length);
  endfunction
endclass
```
</details>

**[실습 3-3] 조건부 제약 도전 (도전)** — 약 30분

`burst_packet`에 `constraint` 하나를 추가하세요: "burst_type이 WRAP(2)일 때, burst_length는 2, 4, 8 중 하나여야 한다." `randomize() with` 절을 사용하여 WRAP 타입만 생성되도록 테스트하세요.

<details>
<summary>힌트</summary>

조건부 제약 조건: `if (burst_type == 2) burst_length inside {2, 4, 8};`. with 절: `pkt.randomize() with { burst_type == 2; };`
</details>

<details>
<summary>모범 답안</summary>

```systemverilog
// burst_packet 클래스에 추가할 제약 조건:
constraint wrap_length_c {
  if (burst_type == 2) burst_length inside {2, 4, 8};
}

// 테스트 코드 (initial begin 블록에 추가):
burst_packet bpkt = new();
$display("=== WRAP 버스트만 생성 ===");
for (int i = 0; i < 5; i++) begin
  if (!bpkt.randomize() with { burst_type == 2; })
    $display("ERROR: 랜덤화 실패!");
  bpkt.display(i);
  // burst_length가 2, 4, 8 중 하나인지 확인하세요!
end
```
</details>

### 흔한 컴파일 에러

코드를 입력하다가 이런 에러가 발생하면:

| 에러 메시지 | 원인 | 해결 |
|------------|------|------|
| `near "endmodule": syntax error` | `endclass`를 빠뜨림 | 모든 class는 `endclass`로 닫기 |
| `near "extends": syntax error` | `extends` 오타 또는 부모 클래스명 오타 | 철자 확인 |
| `null object access` | `new()` 없이 메서드 호출 | 객체 생성 후 사용 |

### 용어 정리

| 한글 용어 | 영어 | 설명 |
|-----------|------|------|
| 클래스 | Class | 데이터와 함수를 묶은 설계도 |
| 객체 | Object | 클래스로부터 생성된 실체 |
| 핸들 | Handle | 객체를 가리키는 참조 (C++ 포인터와 유사) |
| 상속 | Inheritance | 부모 클래스의 기능을 물려받는 것 |
| 다형성 | Polymorphism | 부모 타입으로 자식 객체를 다룰 수 있는 성질 |
| 인터페이스 | Interface | 관련 신호를 묶어서 관리하는 구조 |
| 랜덤화 | Randomization | 변수 값을 자동으로 랜덤 생성 |
| 순환 랜덤 | Cyclic Random | 모든 값을 한 번씩 순회 후 반복하는 랜덤 |
| 제약 조건 | Constraint | 랜덤 값의 범위/규칙을 정의 |
| 열거형 | Enum | 이름으로 상태를 표현하는 타입 |
| 구조체 | Struct | 관련 데이터를 하나로 묶은 타입 |
| 타입 정의 | Typedef | 사용자 정의 타입 이름 부여 |
| 동적 큐 | Queue | 가변 크기 배열 (`[$]`로 선언) |

### 다음 챕터 미리보기

> Chapter 4에서는 다음 내용을 학습합니다:
> - `uvm_component`와 `uvm_object`의 차이
> - 팩토리(Factory) 패턴의 동작 원리 — `new()` 대신 `type_id::create()`를 쓰는 이유
> - 페이즈(Phase) 메커니즘 심화 — `build_phase`, `connect_phase`, `run_phase`의 실행 순서
>
> 이 챕터에서 배운 클래스, 상속, 다형성이 Chapter 4의 핵심 기반입니다.
