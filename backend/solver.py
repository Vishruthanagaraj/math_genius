
import random
import re
from sympy import Eq, symbols, simplify, diff, integrate, solve, factor, expand, sympify
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

x, y, z = symbols("x y z")
TRANSFORMS = standard_transformations + (implicit_multiplication_application,)

def _norm(expr: str) -> str:
    return expr.replace("^", "**").replace("×", "*").replace("÷", "/").strip()

def _parse(expr: str):
    return parse_expr(_norm(expr), transformations=TRANSFORMS, local_dict={"x": x, "y": y, "z": z})

def _pretty(obj) -> str:
    return str(obj).replace("**", "^")

def _plain(s: str) -> str:
    return s.replace("*", " × ").replace("**", "^")

def explain_question(question: str):
    q = question.strip()
    ql = q.lower().strip()

    # evaluate x^2 when x = 4
    m = re.match(r"evaluate\s+(.+)\s+when\s+([xyz])\s*=\s*([\-\d.]+)", ql)
    if m:
        expr_raw, var_name, value = m.groups()
        expr = _parse(expr_raw)
        var = {"x": x, "y": y, "z": z}[var_name]
        num = float(value) if "." in value else int(value)
        substituted = expr.subs(var, num)
        result = simplify(substituted)
        steps = [
            f"We begin with the expression {_pretty(expr)}.",
            f"The question says {var_name} = {value}, so we replace every {var_name} with {value}.",
            f"After substitution, the expression becomes {_pretty(substituted)}.",
            f"Now we do the arithmetic carefully and get {_pretty(result)}."
        ]
        note = "Evaluation means replacing a variable with a known number and then simplifying."
        return steps, _pretty(result), note

    if ql.startswith("simplify "):
        expr = _parse(q[9:])
        result = simplify(expr)
        steps = [
            f"We start with {_pretty(expr)}.",
            "Now we look for like terms. Like terms are parts that have the same variable and the same power.",
            "We combine those like terms so the expression becomes shorter and cleaner.",
            f"After simplifying, the result is {_pretty(result)}."
        ]
        note = "Simplifying does not change the value. It only rewrites the same expression more neatly."
        return steps, _pretty(result), note

    if ql.startswith("expand "):
        expr = _parse(q[7:])
        result = expand(expr)
        steps = [f"We start with {_pretty(expr)}."]
        # Special case for two binomials
        raw = q[7:].strip()
        m2 = re.match(r"\((.+)\)\((.+)\)", raw.replace(" ", ""))
        if m2:
            steps += [
                "Expanding means every term in the first bracket must multiply every term in the second bracket.",
                "Think of it as: first × first, first × second, second × first, second × second.",
                f"After multiplying all parts and combining like terms, we get {_pretty(result)}."
            ]
        else:
            steps += [
                "We remove the brackets by multiplying each outside factor with every term inside.",
                f"After multiplying and combining like terms, we get {_pretty(result)}."
            ]
        note = "Expansion opens brackets so the expression is written as a sum or difference of terms."
        return steps, _pretty(result), note

    if ql.startswith("factorize ") or ql.startswith("factor "):
        expr = _parse(q.split(" ", 1)[1])
        result = factor(expr)
        steps = [f"We begin with {_pretty(expr)}."]
        if "^2" in _pretty(expr):
            steps += [
                "Factorizing means reversing expansion.",
                "We look for simpler expressions that multiply together to make the original expression.",
                f"The expression can be written as {_pretty(result)}."
            ]
        else:
            steps += [
                "We look for a common factor or a pattern such as a difference of squares.",
                f"The factorized form is {_pretty(result)}."
            ]
        note = "Factorizing rewrites an expression as multiplication. This is useful for solving equations and seeing structure."
        return steps, _pretty(result), note

    if ql.startswith("differentiate "):
        expr = _parse(q[14:])
        result = diff(expr, x)
        steps = [
            f"We treat {_pretty(expr)} as a function of x.",
            "Differentiate one term at a time.",
            "For powers of x, use the power rule: bring the power down in front, then reduce the power by 1.",
            f"After applying the rule to each term and simplifying, the derivative is {_pretty(result)}."
        ]
        note = "Differentiation tells us how quickly the expression changes as x changes."
        return steps, _pretty(result), note

    if ql.startswith("integrate "):
        expr = _parse(q[10:])
        result = integrate(expr, x)
        steps = [
            f"We treat {_pretty(expr)} as a function of x.",
            "Integrate one term at a time.",
            "For powers of x, add 1 to the power and divide by the new power.",
            f"After integrating each term, we get {_pretty(result)}.",
            "Because many different functions can have the same derivative, we add the constant of integration C."
        ]
        note = "Integration is the reverse of differentiation."
        return steps, _pretty(result) + " + C", note

    # simultaneous equations
    if ql.startswith("solve ") and " and " in ql and "=" in ql:
        raw = q[6:]
        parts = re.split(r"\band\b", raw, flags=re.IGNORECASE)
        equations = []
        vars_found = set()
        for part in parts:
            left, right = part.split("=", 1)
            l_expr = _parse(left)
            r_expr = _parse(right)
            equations.append(Eq(l_expr, r_expr))
            vars_found |= set(l_expr.free_symbols | r_expr.free_symbols)
        vars_list = sorted(vars_found, key=lambda s: s.name)
        sol = solve(equations, vars_list, dict=True)
        if not sol:
            return ["We formed both equations correctly.", "But there is no pair of values that makes both equations true at the same time."], "No solution found", "A simultaneous system must satisfy every equation together."
        out = sol[0]
        # make elimination explanation for 2 vars/2 eq
        steps = [
            f"We write the two equations together: {_pretty(equations[0].lhs)} = {_pretty(equations[0].rhs)} and {_pretty(equations[1].lhs)} = {_pretty(equations[1].rhs)}.",
            "Now we solve them together because the values of the variables are linked.",
            "A common method is elimination or substitution: remove one variable, solve for the other, then substitute back.",
            f"This gives {', '.join(f'{k} = {v}' for k, v in out.items())}."
        ]
        note = "In simultaneous equations, the final answer must make every equation true, not just one of them."
        return steps, ", ".join(f"{k} = {v}" for k, v in out.items()), note

    if ql.startswith("solve "):
        raw = q[6:]
        if "=" in raw:
            left, right = raw.split("=", 1)
            left_expr = _parse(left)
            right_expr = _parse(right)
            eq = Eq(left_expr, right_expr)
            vars_found = sorted(eq.free_symbols, key=lambda s: s.name)
            target = vars_found[0] if vars_found else x
            moved = simplify(left_expr - right_expr)
            result = solve(eq, target)
            steps = [
                f"We start with the equation {_pretty(left_expr)} = {_pretty(right_expr)}.",
                f"Our goal is to get {target} by itself.",
                f"To make the equation easier to solve, move everything to one side: {_pretty(moved)} = 0.",
            ]
            if len(result) == 1:
                steps.append(f"Now solve that equation. The value that works is {target} = {_pretty(result[0])}.")
                answer = f"{target} = {_pretty(result[0])}"
            else:
                steps.append(f"Now solve the equation. It has more than one valid value: {', '.join(f'{target} = {_pretty(v)}' for v in result)}.")
                answer = ", ".join(f"{target} = {_pretty(v)}" for v in result)
            note = "Solving an equation means finding the value that makes the left side and right side equal."
            return steps, answer, note

        expr = _parse(raw)
        result = solve(expr, x)
        answer = ", ".join(f"x = {_pretty(v)}" for v in result)
        steps = [
            f"We read the expression as {_pretty(expr)}.",
            "Because the command is solve, we treat the expression as equal to zero.",
            f"Now we solve for x and get {answer}."
        ]
        note = "If only one expression is given after 'solve', it is understood as expression = 0."
        return steps, answer, note

    try:
        expr = _parse(q)
        result = simplify(expr)
        steps = [
            f"We read the expression as {_pretty(expr)}.",
            "Since no direct command was given, we simplify it in the most natural way.",
            f"The simplified result is {_pretty(result)}."
        ]
        note = "For the clearest output, start with words like solve, simplify, expand, factorize, differentiate, integrate, or evaluate."
        return steps, _pretty(result), note
    except Exception:
        return [
            "I could not clearly understand the operation from the wording.",
            "Try a direct form such as: solve 2x + 5 = 15.",
            "You can also try simplify, expand, factorize, differentiate, integrate, or evaluate."
        ], "Please enter a clearer math question.", "Clear commands help the system decide exactly what to do."

def _rand_non_zero(a, b):
    n = 0
    while n == 0:
        n = random.randint(a, b)
    return n

def get_practice_question(topic: str, difficulty: str):
    topic_key = topic.lower().strip()
    diff_key = difficulty.lower().strip()

    if topic_key == "linear equations":
        # ax + b = c or ax+b = dx+e
        if diff_key == "easy":
            sol = random.randint(-9, 12)
            a = _rand_non_zero(2, 9)
            b = random.randint(-12, 12)
            c = a * sol + b
            q = f"solve {a}x {'+' if b >= 0 else '-'} {abs(b)} = {c}"
            return {"question": q, "expected_answer": f"x = {sol}"}
        elif diff_key == "medium":
            sol = random.randint(-8, 12)
            a = _rand_non_zero(2, 8)
            d = _rand_non_zero(1, 6)
            while a == d:
                d = _rand_non_zero(1, 6)
            b = random.randint(-10, 10)
            e = a*sol + b - d*sol
            q = f"solve {a}x {'+' if b >= 0 else '-'} {abs(b)} = {d}x {'+' if e >= 0 else '-'} {abs(e)}"
            return {"question": q, "expected_answer": f"x = {sol}"}
        else:
            sol = random.choice([i for i in range(-8, 9) if i not in (0,)])
            denom = random.choice([2, 3, 4, 5, 6, 7, 8])
            p = random.randint(2, 9)
            qv = p*sol - denom*(sol)
            rhs = p - denom
            # (px + q)/d = rhs
            q = f"solve ({p}x {'+' if qv >= 0 else '-'} {abs(qv)})/{denom} = {rhs}"
            return {"question": q, "expected_answer": f"x = {sol}"}

    if topic_key == "expansion":
        if diff_key == "easy":
            a = random.randint(1, 9); b = random.randint(1, 9)
            q = f"expand (x + {a})(x + {b})"
        elif diff_key == "medium":
            a = _rand_non_zero(2, 5); b = random.randint(-9, 9); c = random.randint(-9, 9)
            q = f"expand ({a}x {'+' if b >= 0 else '-'} {abs(b)})(x {'+' if c >= 0 else '-'} {abs(c)})"
        else:
            a = _rand_non_zero(2, 5); b = _rand_non_zero(2, 5); c = random.randint(-8, 8); d = random.randint(-8, 8)
            q = f"expand ({a}x {'+' if c >= 0 else '-'} {abs(c)})({b}x {'+' if d >= 0 else '-'} {abs(d)})"
        ans = _pretty(expand(_parse(q[7:])))
        return {"question": q, "expected_answer": ans}

    if topic_key == "factorization":
        if diff_key == "easy":
            r1, r2 = random.randint(1, 9), random.randint(1, 9)
            expr = expand((x+r1)*(x+r2))
        elif diff_key == "medium":
            r1, r2 = random.randint(-9, -1), random.randint(1, 9)
            expr = expand((x+r1)*(x+r2))
        else:
            a = random.choice([2,3,4]); b = random.randint(1,9)
            expr = expand((a*x-b)*(a*x+b))
        q = f"factorize {_pretty(expr)}"
        ans = _pretty(factor(expr))
        return {"question": q, "expected_answer": ans}

    if topic_key == "simultaneous equations":
        xv = random.randint(-6, 9)
        yv = random.randint(-6, 9)
        if diff_key == "easy":
            a,b,c,d = 1,1,1,-1
        elif diff_key == "medium":
            a,b,c,d = random.choice([(2,1,1,-1),(1,2,1,-1),(2,1,1,1)])
        else:
            a,b,c,d = random.choice([(2,3,1,-1),(3,2,2,-1),(2,1,3,-2)])
        e = a*xv + b*yv
        f = c*xv + d*yv
        q = f"solve {a}x {'+' if b >= 0 else '-'} {abs(b)}y = {e} and {c}x {'+' if d >= 0 else '-'} {abs(d)}y = {f}"
        return {"question": q, "expected_answer": f"x = {xv}, y = {yv}"}

    if topic_key == "calculus":
        if random.choice([True, False]):
            # differentiate
            if diff_key == "easy":
                a,b,c = random.randint(1,4), random.randint(-9,9), random.randint(-9,9)
                expr = a*x**2 + b*x + c
            elif diff_key == "medium":
                a,b = random.randint(1,4), random.randint(1,4)
                expr = a*x**3 + b*x**2 + random.randint(-5,5)*x
            else:
                expr = random.randint(1,3)*x**4 + random.randint(1,4)*x**3 - random.randint(1,6)*x**2 + random.randint(-5,5)
            q = f"differentiate {_pretty(expr)}"
            ans = _pretty(diff(expr, x))
        else:
            if diff_key == "easy":
                expr = random.randint(1,5)*x + random.randint(-9,9)
            elif diff_key == "medium":
                expr = random.randint(1,4)*x**2 + random.randint(1,5)*x
            else:
                expr = random.randint(1,4)*x**3 - random.randint(1,5)*x**2 + random.randint(1,6)*x + random.randint(-5,5)
            q = f"integrate {_pretty(expr)}"
            ans = _pretty(integrate(expr, x)) + " + C"
        return {"question": q, "expected_answer": ans}

    raise ValueError("No practice questions available for this topic and difficulty.")

def _normalize_answer_text(s: str) -> str:
    return s.replace("^", "**").replace(" ", "").lower()

def _expr_equal(a: str, b: str) -> bool:
    try:
        return simplify(_parse(a) - _parse(b)) == 0
    except Exception:
        return False

def check_practice_answer(topic: str, question: str, expected_answer: str, user_answer: str):
    expected = expected_answer.strip()
    user = user_answer.strip()
    correct = False

    if not user:
        return {
            "correct": False,
            "feedback": "Please type an answer first.",
            "worked_steps": [],
            "encouragement": "Start by trying your own answer. Then check it."
        }

    topic_key = topic.lower().strip()

    if topic_key == "simultaneous equations":
        correct = _normalize_answer_text(expected) == _normalize_answer_text(user)
    elif topic_key == "linear equations":
        correct = _normalize_answer_text(expected) == _normalize_answer_text(user)
    elif topic_key in ("expansion", "factorization", "calculus"):
        # allow equivalent algebraic forms
        exp_clean = expected.replace(" + C", "")
        usr_clean = user.replace(" + C", "")
        correct = _expr_equal(exp_clean, usr_clean)
        if " + C" in expected:
            correct = correct and ("c" in user.lower())

    if correct:
        feedback = "Correct! Well done. Your answer matches the expected result."
        encouragement = "Excellent work. You understood this one correctly."
    else:
        feedback = f"Not quite yet. The expected answer is {expected}."
        encouragement = "Do not worry. Compare your work with the guided solution and try another one."

    worked_steps, answer, beginner_note = explain_question(question)

    return {
        "correct": correct,
        "feedback": feedback,
        "worked_steps": worked_steps,
        "expected_answer": expected,
        "answer": answer,
        "encouragement": encouragement,
        "beginner_note": beginner_note,
    }
