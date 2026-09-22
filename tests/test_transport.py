from __future__ import annotations
import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch
from jev_workflow.transport import main, retry_delay

class TransportTests(unittest.TestCase):
    def test_redirect_is_not_followed(self):
        conn = MagicMock()
        response = conn.getresponse.return_value
        response.status = 302
        response.getheader.return_value = None
        stream = MagicMock(); stream.buffer = io.BytesIO(b"{}")
        with patch("jev_workflow.transport.http.client.HTTPSConnection", return_value=conn), patch("sys.stdin", stream), patch.dict(os.environ, {"TYPESAFE_API_KEY": "testing-credential"}), redirect_stdout(io.StringIO()) as output:
            main()
        result = json.loads(output.getvalue())
        self.assertFalse(result["ok"])
        self.assertEqual(result["http_status"], 302)
        self.assertEqual(conn.request.call_count, 1)
        response.read.assert_not_called()
    def test_oversize_response_rejected(self):
        conn = MagicMock()
        conn.getresponse.return_value.status = 200
        conn.getresponse.return_value.read.return_value = b"x" * 65537
        stream = MagicMock(); stream.buffer = io.BytesIO(b"{}")
        with patch("jev_workflow.transport.http.client.HTTPSConnection", return_value=conn), patch("sys.stdin", stream), patch.dict(os.environ, {"TYPESAFE_API_KEY": "testing-credential"}), redirect_stdout(io.StringIO()) as output:
            main()
        self.assertEqual(json.loads(output.getvalue())["reason"], "response_too_large")
    def test_retry_delay_parsing(self):
        self.assertEqual(retry_delay("5"), 5)
        self.assertIsNone(retry_delay("nonsense"))
        self.assertIsNone(retry_delay(None))

if __name__ == "__main__":
    unittest.main()
