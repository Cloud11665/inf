import json
from argparse import ArgumentError
from datetime import datetime
from typing import Tuple, Iterable, Union, Any
from dataclasses import dataclass, asdict, fields, field
from pprint import pprint
import os
import threading
import tempfile
import time
from http.server import CGIHTTPRequestHandler
import socketserver

def dataclass_from_dict(klass, d):
	try:
		fieldtypes = {f.name:f.type for f in fields(klass)}
		return klass(**{f:dataclass_from_dict(fieldtypes[f],d[f]) for f in d})
	except:
		return d

@dataclass(repr=True)
class Person:
	__cnt = 0
	pesel: str
	name: Tuple[str, str]
	birthdate: Union[datetime,int]
	gender: bool

	def __setattr__(self, name: str, value: Any) -> None:
		if name == "gender":
			if self.__cnt:
				raise ArgumentError(None, message="sneed harder")
			self.__cnt += 1
		self.__dict__[name] = value

@dataclass(repr=True)
class TeamMember(Person):
	function: Union[str,None] = None
	join_date: Union[datetime,None,int] = None

@dataclass(repr=True)
class TeamLeader(Person):
	experience: int

@dataclass(repr=True)
class Team:
	name: str
	leader: TeamLeader
	members: Iterable[TeamMember] = field(default_factory=list)


#team = Team("foo",TeamLeader("asd",("jef","who"),datetime.now(),True,10))
team = None

class HTTPHandler(CGIHTTPRequestHandler):
	def do_GET(self):
		global team
		tokens = self.path.split("/")
		tokens = [*filter(lambda x:x, tokens)]
		tokens = [*map(lambda x:x.lower(), tokens)]

		if len(tokens) == 1:
			if tokens[0] == "team":
				if team is not None:
					self.send_response(200)
					self.send_header("Content-type", "application/json")
					self.send_header("Access-Control-Allow-Origin", "*")
					self.end_headers()
					print(team)
					self.wfile.write(json.dumps(asdict(team),
							default=lambda x:int(x.timestamp()),
							indent=1
							).encode("utf-8")
						)
				else:
					self.send_error(404, "The team hasnt been created yet.")
					self.send_header("Access-Control-Allow-Origin", "*")
					self.end_headers()

	def do_POST(self):
		global team
		tokens = self.path.split("/")
		tokens = [*filter(lambda x:x, tokens)]
		tokens = [*map(lambda x:x.lower(), tokens)]

		#pprint(dict(self.headers))
		con_len = self.headers.get("Content-Length", "0")
		con_len = int(con_len)

		data = self.rfile.read(con_len)
		data = data.decode("utf-8")
		data = json.loads(data)
		#pprint(data)

		if len(tokens) == 1:
			if tokens[0] in ["create","edit"]:
				team = dataclass_from_dict(Team, data)
				print(team)
				self.send_response(200)
				self.send_header("Content-type", "application/json")
				self.send_header("Access-Control-Allow-Origin", "*")
				self.end_headers()
			else:
				self.send_error(404, "Operation not supported")
				self.end_headers()

handle = HTTPHandler
srv_addr = ("localhost", 5000)


fh = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".html")
fh.write("""
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>kosz-work</title>
</head>
<body>
	<h1>kosz-work</h1>
	<img src="https://media.discordapp.net/attachments/688875736643272920/834533997861797949/ezgif-4-2818f2d02688.gif" width="20%">
	<br>
	<label for="zname">nazwa zespolu</label>
	<input type="text" id="zname" value="soyjaks" oninput="send_data()"><br>

	<p style="margin: 10 0 0 0">szefuncio:</p>
	<label for="bname">imie</label>
	<input type="text" id="bname" value="pajeet" oninput="send_data()"><br>
	<label for="bsname">nazwisko</label>
	<input type="text" id="bsname" value="rustacan" oninput="send_data()"><br>
	<label for="bdate">data urodzenia</label>
	<input type="date" id="bdate" value="2010-06-07" oninput="send_data()"><br>
	<label for="bgender">płeć (1 to chłop)</label>
	<input type="checkbox" id="bgender" oninput="send_data()"><br>
	<label for="bpesel">pesel</label>
	<input type="text" id="bpesel" value="89023481238092" oninput="send_data()"><br>
	<label for="bexp">doświadczenie</label>
	<input type="number" min="0" max="1337" id="bexp" oninput="send_data()"><br>

	<p style="margin: 10 0 0 0">pracownicy:</p>
	<div id="wagies" style="margin: 0 0 0 10">

	</div>
	<button onclick="addwagie()">add wagie</button>
	<button onclick="rmwagie()">remove wagie</button>

	<p>JSON:</p>
	<textarea id="code" spellcheck="false" cols="80" rows="30" oninput="syncjson(this)">

	</textarea>
	</body>
	<script>
		var url = "http://localhost:5000"

		function update(resp) {
			document.getElementById("code").value = JSON.stringify(resp, null, "  ")
			document.getElementById("zname").value = resp.name
			document.getElementById("bname").value = resp.leader.name[0]
			document.getElementById("bsname").value= resp.leader.name[1]
			document.getElementById("bdate").value = new Date(resp.leader.birthdate).toISOString().split('T')[0]
			document.getElementById("bgender").value = resp.leader.gender
			document.getElementById("bgender").checked = resp.leader.gender ? "checked" : ""
			document.getElementById("bpesel").value = resp.leader.pesel
			document.getElementById("bexp").value = resp.leader.experience

			document.getElementById("wagies").innerHTML = ""
			for (const wagie of resp.members) {
				var xmlstring = `
					<div class="wagie">
						<label for="wname">imie</label>
						<input type="text" class="wname" value="${wagie.name[0]}" oninput="send_data()"><br>
						<label for="wsname">nazwisko</label>
						<input type="text" class="wsname" value="${wagie.name[1]}" oninput="send_data()"><br>
						<label for="wdate">data urodzenia</label>
						<input type="date" class="wdate" value="${new Date(wagie.birthdate).toISOString().split('T')[0]}" oninput="send_data();this.focus()"><br>
						<label for="wgender">płeć (1 to chłop)</label>
						<input type="checkbox" class="wgender" value="${wagie.gender}" ${wagie.gender?"checked":""} oninput="send_data()"><br>
						<label for="wpesel">pesel</label>
						<input type="text" class="wpesel" value="${wagie.pesel}" oninput="send_data()"><br>
						<label for="wrole">rola w zespole</label>
						<input type="text" class="wrole" value="${wagie.function}" oninput="send_data()"><br>
						<label for="wjoin">data dołączenia</label>
						<input type="date" class="wjoin" value="${new Date(wagie.join_date).toISOString().split('T')[0]}" oninput="send_data()"><br>
						<br>
					</div>
				`
				document.getElementById("wagies").innerHTML += xmlstring
			}
		}

		const xhrget = new XMLHttpRequest();
		xhrget.onload = ()=>{
			const resp = JSON.parse(xhrget.response)
			update(resp)
			document.getElementById("code").value = JSON.stringify(resp, null, "  ")
		}

		xhrget.open("GET", `${url}/team`);
		xhrget.send()


		function send_data() {
			const xhr = new XMLHttpRequest();

			params = {
				name: document.getElementById("zname").value,
				leader: {
					pesel: document.getElementById("bpesel").value,
					name: [
						document.getElementById("bname").value,
						document.getElementById("bsname").value
					],
					birthdate: new Date(document.getElementById("bdate").value).valueOf(),
					gender: document.getElementById("bgender").checked,
					experience: document.getElementById("bexp").value
				},
				members: []
			}

			memb = Array.from(document.querySelectorAll(".wagie"))
			for (const wagie of memb) {
				temp = {
					pesel: wagie.querySelectorAll(".wpesel")[0].value,
					name: [
						wagie.querySelectorAll(".wname")[0].value,
						wagie.querySelectorAll(".wsname")[0].value
					],
					birthdate: new Date(wagie.querySelectorAll(".wdate")[0].value).valueOf(),
					gender: wagie.querySelectorAll(".wgender")[0].checked,
					function: wagie.querySelectorAll(".wrole")[0].value,
					join_date: new Date(wagie.querySelectorAll(".wjoin")[0].value).valueOf()
				}
				params.members.push(temp)
			}

			document.getElementById("code").value = JSON.stringify(params, null, "  ")
			console.log(params)

			xhr.open("POST", `${url}/edit`);
			xhr.send(JSON.stringify(params))
		}

		function rmwagie() {
			var wagie = document.getElementById("wagies").children
			wagie.item(wagie.length-1).remove()
			send_data()
		}

		function addwagie() {
			var xmlstring = `
				<div class="wagie">
					<label for="wname">imie</label>
					<input type="text" class="wname" value="" oninput="send_data()"><br>
					<label for="wsname">nazwisko</label>
					<input type="text" class="wsname" value="" oninput="send_data()"><br>
					<label for="wdate">data urodzenia</label>
					<input type="date" class="wdate" value="" oninput="send_data()"><br>
					<label for="wgender">płeć (1 to chłop)</label>
					<input type="checkbox" class="wgender" value="" oninput="send_data()"><br>
					<label for="wpesel">pesel</label>
					<input type="text" class="wpesel" value="" oninput="send_data()"><br>
					<label for="wrole">rola w zespole</label>
					<input type="text" class="wrole" value="" oninput="send_data()"><br>
					<label for="wjoin">data dołączenia</label>
					<input type="date" class="wjoin" value="" oninput="send_data()"><br>
					<br>
				</div>
			`
			document.getElementById("wagies").innerHTML += xmlstring
			send_data()
		}

		function syncjson(e) {
			const xhr = new XMLHttpRequest();
			var params = JSON.parse(e.value)
			console.log(params)
			xhr.open("POST", `${url}/edit`);
			xhr.send(JSON.stringify(params))

			const xhrget = new XMLHttpRequest();
			xhrget.onload = ()=>{
				const resp = JSON.parse(xhrget.response)
				update(resp)
			}

			xhrget.open("GET", `${url}/team`);
			xhrget.send()
		}

		send_data()
	</script>
</html>
""")
fh.flush()
print("Jesli nie pojawilo sie okno, otworz plik", fh.name, "w przegladarce.")

if os.name == "nt":
	exe = f"C:\\\"Program Files (x86)\"\\Google\\Chrome\\Application\\chrome.exe --app=\"{fh.name}\""
else:
	exe = f"x-www-browser --app=\"file://{fh.name}\""

threading.Thread(target=os.system, args=(exe,), name="gui", daemon=True).start()

with socketserver.TCPServer(srv_addr, handle) as httpd:
	print(f"Running on http://{srv_addr[0]}:{srv_addr[1]}")
	while True:
		try:
			httpd.serve_forever()
		except OSError:
			time.sleep(3)
		except KeyboardInterrupt:
			httpd.shutdown()
			exit(0)

