import json
from http.server import HTTPServer, BaseHTTPRequestHandler

DEFAULT_USER = {
    "id": 1,
    "username": "theUser",
    "firstName": "John",
    "lastName": "James",
    "email": "john@email.com",
    "password": "12345",
}

USERS_LIST = [dict(DEFAULT_USER)]


def is_valid_user_dict(data):
    if not isinstance(data, dict):
        return False
    required_keys = {"id", "username", "firstName", "lastName", "email", "password"}
    if set(data.keys()) != required_keys:
        return False
    return (
        isinstance(data["id"], int)
        and isinstance(data["username"], str)
        and isinstance(data["firstName"], str)
        and isinstance(data["lastName"], str)
        and isinstance(data["email"], str)
        and isinstance(data["password"], str)
    )


def is_valid_update_dict(data):
    if not isinstance(data, dict):
        return False
    required_keys = {"username", "firstName", "lastName", "email", "password"}
    if set(data.keys()) != required_keys:
        return False
    return (
        isinstance(data["username"], str)
        and isinstance(data["firstName"], str)
        and isinstance(data["lastName"], str)
        and isinstance(data["email"], str)
        and isinstance(data["password"], str)
    )


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def _set_response(self, status_code=200, body=None):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(body if body is not None else {}).encode('utf-8'))

    def _pars_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return None
        try:
            return json.loads(self.rfile.read(content_length).decode('utf-8'))
        except Exception:
            return None

    def do_GET(self):
        global USERS_LIST

        if self.path == "/reset":
            USERS_LIST = [dict(DEFAULT_USER)]
            self._set_response(200, USERS_LIST)

        elif self.path == "/users":
            self._set_response(200, USERS_LIST)

        elif self.path.startswith("/user/"):
            username = self.path[len("/user/"):]
            user = next((u for u in USERS_LIST if u["username"] == username), None)
            if user:
                self._set_response(200, user)
            else:
                self._set_response(400, {"error": "User not found"})

        else:
            self._set_response(404, {"error": "Not found"})

    def do_POST(self):
        data = self._pars_body()

        if self.path == "/user":
            if not is_valid_user_dict(data):
                self._set_response(400, {})
                return

            if any(u["id"] == data["id"] for u in USERS_LIST):
                self._set_response(400, {})
                return

            USERS_LIST.append(data)
            self._set_response(201, data)

        elif self.path == "/user/createWithList":
            if not isinstance(data, list) or len(data) == 0:
                self._set_response(400, {})
                return

            for item in data:
                if not is_valid_user_dict(item):
                    self._set_response(400, {})
                    return

            existing_ids = {u["id"] for u in USERS_LIST}
            new_ids = [item["id"] for item in data]

            if len(new_ids) != len(set(new_ids)) or any(id_val in existing_ids for id_val in new_ids):
                self._set_response(400, {})
                return

            USERS_LIST.extend(data)
            self._set_response(201, data)

        else:
            self._set_response(400, {})

    def do_PUT(self):
        if self.path.startswith("/user/"):
            id_str = self.path[len("/user/"):]
            if not id_str.isdigit():
                self._set_response(400, {"error": "not valid request data"})
                return

            user_id = int(id_str)
            data = self._pars_body()

            if not is_valid_update_dict(data):
                self._set_response(400, {"error": "not valid request data"})
                return

            user = next((u for u in USERS_LIST if u["id"] == user_id), None)
            if not user:
                self._set_response(404, {"error": "User not found"})
                return

            user.update(data)
            self._set_response(200, user)
        else:
            self._set_response(404, {"error": "User not found"})

    def do_DELETE(self):
        if self.path.startswith("/user/"):
            id_str = self.path[len("/user/"):]
            if id_str.isdigit():
                user_id = int(id_str)
                user = next((u for u in USERS_LIST if u["id"] == user_id), None)
                if user:
                    USERS_LIST.remove(user)
                    self._set_response(200, {})
                    return

        self._set_response(404, {"error": "User not found"})


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, host='localhost', port=8000):
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
