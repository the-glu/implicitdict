import multiprocessing
from typing import List, Optional, Type
from implicitdict import ImplicitDict
from implicitdict.jsonschema import make_json_schema, SchemaVars


class ResponseType(ImplicitDict):
    pass


class Query(ImplicitDict):

    participant_id: Optional[str]
    """If specified, identifier of the USS/participant hosting the server involved in this query."""

    def parse_json_result(self, parse_type: Type[ResponseType]) -> ResponseType:
        """Parses the JSON result into the specified type.

        Args:
            parse_type: ImplicitDict type to parse into.
        Returns:
             the parsed response (of type `parse_type`).
        Raises:
            QueryError: if the parsing failed.
        """
        try:
            return parse_type(ImplicitDict.parse(self.response.json, parse_type))
        except (ValueError, TypeError, KeyError) as e:
            raise QueryError(
                f"Parsing JSON response into type {parse_type.__name__} failed with exception {type(e).__name__}: {e}",
                self,
            )


class QueryError(RuntimeError):
    """Error encountered when interacting with a server in the UTM ecosystem."""

    queries: List[Query]


def _perform_docstring_parsing_test():
    repo = {}
    make_json_schema(Query, lambda t: SchemaVars(name=t.__name__), repo)


def test_docpattern():
    """Tests issue #13 'Regex gets incorrect matches'"""

    # Perform actual test in separate process with timeout
    test_process = multiprocessing.Process(target=_perform_docstring_parsing_test, args=[])
    test_process.start()
    test_process.join(timeout=1)
    assert test_process.exitcode is not None, "make_json_schema did not complete within the time limit"
