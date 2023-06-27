import csv
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from datetime import datetime

class SimpleServer(BaseHTTPRequestHandler):
    propresenter_address = ''

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
                <html>
                <body>
                <h2>Child Information</h2>
                <form method="POST" action="/submit">
                Child Number: <input type="text" name="child_number" pattern="\d{3}" required><br>
                Room:
                <select name="room">
                <option value="Nursery">Nursery</option>
                <option value="2's &amp; 3's">2's &amp; 3's</option>
                <option value="4-K">4-K</option>
                <option value="1st-5th">1st-5th</option>
                </select><br>
                <input type="submit" value="Submit">
                </form>
                <a href="/list">View Paging Requests</a>
                </body>
                </html>
            ''')
        elif self.path == '/list':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
                <html>
                <head>
                <script>
                function updateTime() {
                    var clock = document.getElementById("clock");
                    var now = new Date();
                    clock.textContent = now.toLocaleString();
                }
                setInterval(updateTime, 1000);
                </script>
                </head>
                <body>
                <h2>Paging Requests</h2>
                <p>ProPresenter Address: <input type="text" id="propresenter_address" placeholder="ProPresenter Address"></p>
                <p id="clock"></p>
                <table>
                <tr>
                    <th>Child Number</th>
                    <th>Room</th>
                    <th>Timestamp</th>
                    <th>Age (Minutes)</th>
                    <th>Action</th>
                </tr>
            ''')

            if 'propresenter_address' in parse_qs(urlparse(self.path).query):
                self.propresenter_address = parse_qs(urlparse(self.path).query)['propresenter_address'][0]
            
            with open('child_info.csv', 'r') as file:
                reader = csv.reader(file)
                rows = list(reader)
                for row in rows:
                    child_number = row[0]
                    room = row[1]
                    timestamp = row[2]
                    age = int((datetime.now() - datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')).total_seconds() / 60)
                    self.wfile.write(f'<tr><td>{child_number}</td><td>{room}</td><td>{timestamp}</td><td>{age}</td>'.encode('utf-8'))
                    self.wfile.write(b'''
                        <td>
                            <button onclick="sendToProPresenter(this)">Send to ProPresenter</button>
                        </td>
                        </tr>
                    ''')

            self.wfile.write(b'''
                </table>
                <script>
                function sendToProPresenter(button) {
                    var row = button.parentNode.parentNode;
                    var childNumber = row.getElementsByTagName("td")[0].innerText;
                    var room = row.getElementsByTagName("td")[1].innerText;
                    var propresenterAddress = document.getElementById("propresenter_address").value;
                    
                    var url = 'http://' + propresenterAddress + '/v1/message/CityKidsPager/trigger';
                    var payload = [
                        {
                            "name": "Child#",
                            "text": {
                                "text": childNumber
                            }
                        },
                        {
                            "name": "Room",
                            "text": {
                                "text": room
                            }
                        }
                    ];

                    var xhr = new XMLHttpRequest();
                    xhr.open("POST", url, true);
                    xhr.setRequestHeader("Content-Type", "application/json");
                    xhr.send(JSON.stringify(payload));

                    xhr.onreadystatechange = function () {
                        if (xhr.readyState === XMLHttpRequest.DONE) {
                            if (xhr.status === 204) {
                                alert("Message sent to ProPresenter successfully.");
                                row.parentNode.removeChild(row);
                            } else {
                                alert("Error sending message to ProPresenter.");
                            }
                        }
                    };
                }
                </script>
                </body>
                </html>
            ''')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')

    def do_POST(self):
        if self.path == '/submit':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            child_number = params['child_number'][0]
            room = params['room'][0]
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Write data to CSV file
            data = [child_number, room, timestamp]
            with open('child_info.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(data)

            self.wfile.write(b'''
                <html>
                <body>
                <h2>Success</h2>
                <p>Data submitted successfully!</p>
                <a href="/">Back</a>
                </body>
                </html>
            ''')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')

def run_server():
    host = 'localhost'
    port = 8000
    server_address = (host, port)
    httpd = HTTPServer(server_address, SimpleServer)
    print(f'Starting server on {host}:{port}...')
    httpd.serve_forever()

run_server()