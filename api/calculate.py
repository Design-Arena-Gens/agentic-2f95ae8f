import json
import math
import ast
from http.server import BaseHTTPRequestHandler


SAFE_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "log": math.log,
    "ln": math.log,
    "log10": math.log10,
    "sqrt": math.sqrt,
    "cbrt": lambda x: math.pow(x, 1 / 3),
    "exp": math.exp,
    "abs": abs,
    "floor": math.floor,
    "ceil": math.ceil,
    "round": round,
    "deg": math.degrees,
    "rad": math.radians,
}


def _factorial(x: float) -> float:
    if int(x) != x or x < 0:
        raise ValueError("Factorial is only defined for non-negative integers.")
    return math.factorial(int(x))


SAFE_FUNCTIONS["fact"] = _factorial
SAFE_FUNCTIONS["factorial"] = _factorial
SAFE_FUNCTIONS["sin_deg"] = lambda x: math.sin(math.radians(x))
SAFE_FUNCTIONS["cos_deg"] = lambda x: math.cos(math.radians(x))
SAFE_FUNCTIONS["tan_deg"] = lambda x: math.tan(math.radians(x))
SAFE_FUNCTIONS["asin_deg"] = lambda x: math.degrees(math.asin(x))
SAFE_FUNCTIONS["acos_deg"] = lambda x: math.degrees(math.acos(x))
SAFE_FUNCTIONS["atan_deg"] = lambda x: math.degrees(math.atan(x))


SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Pow,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.FloorDiv,
    ast.USub,
    ast.UAdd,
    ast.Assign,
    ast.Store,
    ast.arguments,
    ast.keyword,
    ast.Tuple,
    ast.List,
)


class EvaluationError(ValueError):
    """Raised when the expression is invalid."""


def _validate_node(node: ast.AST) -> None:
    if not isinstance(node, ALLOWED_NODES):
        raise EvaluationError(f"Unsupported expression element: {type(node).__name__}")
    for child in ast.iter_child_nodes(node):
        _validate_node(child)


def evaluate_expression(expression: str) -> float:
    if not expression or not isinstance(expression, str):
        raise EvaluationError("Expression is empty.")

    parsed = ast.parse(expression, mode="eval")
    _validate_node(parsed)
    compiled = compile(parsed, "<expr>", "eval")
    safe_globals = {"__builtins__": {}}
    safe_locals = {**SAFE_FUNCTIONS, **SAFE_CONSTANTS}
    try:
        result = eval(compiled, safe_globals, safe_locals)
    except ZeroDivisionError as exc:
        raise EvaluationError("Division by zero.") from exc
    except ValueError as exc:
        raise EvaluationError(str(exc)) from exc
    except OverflowError as exc:
        raise EvaluationError("Result overflow.") from exc
    except Exception as exc:
        raise EvaluationError("Invalid expression.") from exc

    if isinstance(result, complex):
        raise EvaluationError("Complex results are not supported.")
    return float(result)


def _make_response(status: int, payload: dict) -> bytes:
    response = json.dumps(payload).encode("utf-8")
    return status, response


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self._write_cors_headers()
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"
            data = json.loads(raw_body.decode("utf-8"))
            expression = data.get("expression", "")
            result = evaluate_expression(expression)
            status, body = _make_response(200, {"result": result})
        except json.JSONDecodeError:
            status, body = _make_response(400, {"error": "Invalid JSON payload."})
        except EvaluationError as exc:
            status, body = _make_response(400, {"error": str(exc)})
        except Exception:
            status, body = _make_response(500, {"error": "Internal server error."})

        self.send_response(status)
        self._write_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        status, body = _make_response(
            200,
            {
                "message": "Scientific calculator API. Send POST requests with "
                '{"expression": "<expression>"} to evaluate.',
                "available_functions": sorted(SAFE_FUNCTIONS.keys()),
                "available_constants": sorted(SAFE_CONSTANTS.keys()),
            },
        )
        self.send_response(status)
        self._write_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return

    def _write_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
