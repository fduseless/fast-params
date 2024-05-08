import re
from typing import Any, Dict
from starlette.datastructures import ImmutableMultiDict


class ParamsTooDeepError(Exception): ...


class ParameterTypeError(Exception): ...


PAT = re.compile(r"\[\]")
PAT2 = re.compile(r"[\[\]]+")


class ParamParser:
    def __init__(self, param_depth_limit: int = 32) -> None:
        self._param_depth_limit = param_depth_limit

    def __call__(self, form: ImmutableMultiDict[str, Any]) -> Dict[str, Any]:
        js = self._make_params()
        for k, v in form.multi_items():
            self._normalize_params(js, k, v)
        return js

    def _normalize_params(
        self, params: Dict[str, Any], name: str, v: Any, depth: int = 0
    ) -> Any:
        if depth >= self._param_depth_limit:
            raise ParamsTooDeepError()
        print(f"params: {params}, name: {name}, v: {v}, depth: {depth}")
        if not name:
            k = after = ""
        elif depth == 0:
            if (start := name.find("[", 1)) >= 0:
                k = name[0:start]
                after = name[start:]
            else:
                k = name
                after = ""
        elif name.startswith("[]"):
            k = "[]"
            after = name[2:]
        elif name.startswith("[") and (start := name.find("]", 1)) >= 0:
            k = name[1:start]
            after = name[start + 1 :]
        else:
            k = name
            after = ""
        if not k:
            return

        if after == "":
            if k == "[]" and depth != 0:
                return [v]
            else:
                params[k] = v
        elif after == "[":
            params[name] = v
        elif after == "[]":
            params[k] = params.get(k) or []
            if not isinstance(params[k], list):
                raise ParameterTypeError(
                    f"expected Array (got {type(params[k])}) for param `{k}'"
                )
            params[k].append(v)
        elif after.startswith("[]"):
            if (
                after[2] == "["
                and after.endswith("]")
                and (child_key := after[3 : len(after) - 4])
                and child_key.find("[") < 0
                and child_key.find("]") < 0
            ):
                pass
            else:
                child_key = after[2:]
            params[k] = params.get(k) or []
            if not isinstance(params[k], list):
                raise ParameterTypeError(
                    f"expected Array (got {type(params[k])}) for param `{k}'"
                )
            if (
                params[k]
                and self._params_hash_type(params[k][-1])
                and not self._params_hash_has_key(params[k][-1], child_key)
            ):
                self._normalize_params(params[k][-1], child_key, v, depth + 1)
            else:
                params[k].append(
                    self._normalize_params(self._make_params(), child_key, v, depth + 1)
                )
        else:
            params[k] = params.get(k) or self._make_params()
            if not self._params_hash_type(params[k]):
                raise ParameterTypeError(
                    f"expected Hash (got {type(params[k])}) for param `{k}'"
                )
            params[k] = self._normalize_params(params[k], after, v, depth + 1)

        return params

    def _make_params(self):
        return dict()

    def _params_hash_type(self, obj) -> bool:
        return isinstance(obj, dict)

    def _params_hash_has_key(self, hash, key) -> bool:
        if PAT.match(key):
            return False
        h = hash
        for part in PAT2.split(key):
            if part == "":
                continue
            if not (self._params_hash_type(h) and part in h):
                return False
            h = h[part]
        return True


DEFAULT_PARSER = ParamParser()
