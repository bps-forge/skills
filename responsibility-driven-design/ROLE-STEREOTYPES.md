# Role Stereotypes

Six stereotypes from Wirfs-Brock's RDD. Use them as a vocabulary, not a taxonomy — most real objects lean toward one but borrow from another. When recommending a role, name the stereotype *and* the borrowed traits.

## 1. Information Holder

Just holds data. Answers questions about itself. No decisions, no orchestration.

- **OO examples:** DTO, Value Object, immutable record
- **Functional approximation:** algebraic data type, record, struct
- **Smell:** an Information Holder that branches on its own state — promote it or extract the decision into a Service Provider

## 2. Structurer

Manages a structure or collection. Maintains invariants across the parts.

- **OO examples:** Aggregate root, collection wrapper, tree manager
- **Functional approximation:** a module owning a data type plus the smart constructors / update functions that preserve its invariants
- **Smell:** a Structurer that lets callers mutate parts directly — the invariant isn't really being enforced

## 3. Service Provider

Does reusable logic or calculation. Stateless or near-stateless. Answers "compute X from Y".

- **OO examples:** Pricing calculator, formatter, encoder
- **Functional approximation:** a module of pure functions; this is the most natural fit in FP
- **Smell:** a Service Provider that talks to the database — that's an Interfacer wearing the wrong hat

## 4. Coordinator

Owns the *sequencing* between collaborators — the choreography. Knows *who* should do what next, in what order, and how to compensate on failure. Doesn't own the policy decision that started the flow.

If the flow itself is predetermined ("first A, then B, then C; on failure roll back"), that's a Coordinator. If the object is choosing *whether* or *which branch* to take based on use-case rules, that's a Controller.

- **OO examples:** Saga, workflow, process manager
- **Functional approximation:** a use-case function that composes calls to other modules; effects pushed to the edges
- **Contrast:** a checkout saga that runs `reserve → charge → ship → confirm` (and compensates on failure) is a **Coordinator**. The object that decided "this order is valid, proceed to checkout" before handing off to the saga is a **Controller**. In small systems the same object plays both roles — that's fine, but name both responsibilities.
- **Smell:** a Coordinator that does business calculation — extract to a Service Provider
- **Smell:** a Coordinator with `if`s on domain state choosing wildly different branches — the policy has leaked in; extract a Controller

## 5. Controller

Makes use-case-level decisions **that direct other objects**. Owns "should we proceed?", "which branch do we take next?", "do we commit or roll back?" at the application boundary — and then acts on the answer by orchestrating collaborators.

If an object just returns a verdict and something else decides what to do with it, that's a Service Provider, not a Controller. The Controller is the thing reading the verdict and routing the flow.

- **OO examples:** Use case / Interactor, application service, command handler
- **Functional approximation:** a use-case function that branches on a tagged result (`Approved | Rejected reason`) and drives the next step
- **Contrast:** a validation rule that returns `Valid | Invalid(reason)` is a **Service Provider**. The component that reads those verdicts and decides "fail the build" is the **Controller**.
- **Smell:** a Controller that also formats output for the wire — split the presentation into an Interfacer
- **Smell:** anything called a "Rule", "Policy", "Validator", "Check", or "Specification" — these almost always compute a verdict from inputs without directing collaborators. Default them to Service Provider unless they actually orchestrate something.

## 6. Interfacer

Bridges the inside and the outside world. Translates between the domain and HTTP / DB / queue / file system / external API.

- **OO examples:** Gateway, repository, presenter, listener, controller-in-the-MVC-sense (yes, the names collide)
- **Functional approximation:** adapter module; impure boundary at the edge of the program
- **Smell:** an Interfacer leaking external types (rows, JSON) inward, or domain types outward — translation is its whole job

---

## Choosing a stereotype — quick decision tree

1. Does it talk to the outside world (FS, DB, HTTP, queue, external API)? → **Interfacer**
2. Does it compute a result, verdict, or value from its inputs — and then stop? → **Service Provider**
   (Returning `Valid | Invalid`, `Approved | Rejected`, a price, a score, a parsed AST — all Service Provider. The decision to *act* on that result is somebody else's job.)
3. Does it direct other objects based on a use-case decision — "do this, then that, otherwise roll back"? → **Controller**
4. Does it route work between collaborators without making the policy call itself? → **Coordinator**
5. Does it own a collection or aggregate's invariants? → **Structurer**
6. Does it just hold data? → **Information Holder**

**SP vs Controller tiebreaker:** ask "does this object tell other objects what to do, or does it just answer a question?" If it just answers a question — even an authoritative-sounding one like "is this allowed?" — it's a Service Provider. The Controller is whoever consumes the answer.

**Controller vs Coordinator tiebreaker:** ask "is this object deciding *whether/which*, or deciding *in what order*?" Controllers branch on policy. Coordinators run a known choreography. If the steps are fixed and the object's job is to march through them (and compensate on failure), it's a Coordinator — even if the steps are complex.

If none of these fit cleanly, the responsibility is probably two responsibilities. Split it.

When you pick **Controller**, name the other stereotype you rejected (almost always Service Provider) and why. This forces the SP/Controller seam to be drawn deliberately instead of by reflex.

## Functional codebases — don't over-apply

In functional or constrained codebases, the stereotypes are *labels for intent*, not classes you have to create. A module of pure functions with one impure boundary function might be three stereotypes in two files. That's fine. Use the labels in the plan doc to communicate intent; let the code shape follow the paradigm.
