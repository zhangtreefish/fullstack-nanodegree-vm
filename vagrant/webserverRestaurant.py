from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
from manyRestaurants import Restaurant, session


class webServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path.endswith("/restaurants"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>"
                output += "<h1> My Restaurants"
                # By adding this next line the newly posted restaurant shows up at the /restaurant page
                restaurant_list=session.query(Restaurant).all()
                for restaurant in restaurant_list:
                    output += "<h2>"+restaurant.name+ "<h4><a href='#'> EDIT </a></h4><h4><a href='#'> DELETE </a></h4>"+"</h2>"
                    # "<a href=''> EDIT </a>"+ "<a href=''> DELETE </a>"
                output += "</h1>"
                # the next 3 lines makes the page blank
                # output += " <h2> Create a new restaurant of your favorite kind: </h2>"
                # output += "<h1> %s </h1>" % messagecontent[0]
                # output += '''<form method='POST' enctype='multipart/form-data' action='/restaurants'><h2>So you created:</h2><input name="message" type="text" ><input type="submit" value="Submit"> </form>'''

                output += "</body></html>"
                self.wfile.write(output)
                # print output
                return

            if self.path.endswith("/restaurants/new"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<html><body>"
                output += "<h2>Hola! Create a new restaurant of your favorite kind:</h2>"
                # TODO: where is the /restaurants/new file?
                output += '''<form method='POST' enctype='multipart/form-data' action='/restaurants/new'><h2>You would create:</h2><input name="message" type="text" ><input type="submit" value="Submit"> </form>'''
                output += "</body></html>"
                self.wfile.write(output)
                print output
                return

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        try:
            if self.path.endswith("/restaurants/new"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('message')

                output = ""
                output += "<html><body>"
                output += " <h2> Created a new restaurant of your favorite kind: </h2>"
                output += "<h1> %s </h1>" % messagecontent[0]

                myNewRestaurant = Restaurant(name=messagecontent[0])
                session.add(myNewRestaurant)
                session.commit()
                restaurant_list=session.query(Restaurant).all()
                for res in restaurant_list:
                    print res.name

                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location', '/restaurants')
                self.end_headers()

                # output += '''<form method='POST' enctype='multipart/form-data' action='/restaurants/new'><h2>And more restaurants you have dreamt to create:</h2><input name="message" type="text" ><input type="submit" value="Submit"> </form>'''
                # output += "</body></html>"
                # self.wfile.write(output)
                # print output
        except:
            pass


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), webServerHandler)
        print "Web Server running on port %s" % port
        server.serve_forever()
    except KeyboardInterrupt:
        print " ^C entered, stopping web server...."
        server.socket.close()

if __name__ == '__main__':
    main()