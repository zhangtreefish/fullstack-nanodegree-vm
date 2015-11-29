from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
from manyRestaurants import Restaurant, session
import logging, sys


class webServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path.endswith("/restaurants"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>"
                output += "<a href='/restaurants/new'> Create a new restaurant </a>"
                output += "<h1> My Restaurants"
                # By adding this next line the newly posted restaurant shows up at the /restaurant page
                restaurant_list=session.query(Restaurant).all()
                for restaurant in restaurant_list:
                    id_number=str(restaurant.id)
                    output += "<h2>"+restaurant.name+\
                    "<h4><a href='/restaurants/"+id_number+"/edit'> EDIT </a></h4>\
                    <h4><a href='/restaurants/"+id_number+"/delete'> DELETE </a></h4></h2>"
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
                # TODO: where is the /restaurants/new file?
                output += '''<form method='POST'
                enctype='multipart/form-data'
                action='/restaurants/new'>
                <h2>New Restaurant:</h2>
                <input name="newRestaurant" type="text" >
                <input type="submit" value="Submit">
                </form>'''
                output += "</body></html>"
                self.wfile.write(output)
                print output
                return

            if self.path.endswith("/edit"):
                laPath = self.path.split('/')
                # print laPath  # ['', 'restaurants', '4', 'edit']
                laPathId = laPath[2]
                myRestaurant = session.query(Restaurant).filter_by(id=laPathId).one()
                if myRestaurant != []:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    output = ""
                    output += "<html><body>"
                    output += "<form method='POST'\
                     enctype='multipart/form-data'\
                     action='/restaurants/%s/edit'>" % str(laPathId)
                    output += "<h2>New Name for %s</h2>" % myRestaurant.name
                    output += "<input name='newName' type='text' >\
                    <input type='submit' value='Submit'>\
                    </form>"
                    output += "</body></html>"
                    self.wfile.write(output)

                    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
                    logging.debug('A debug message!')
                    logging.info('from /edit', output)
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
                    messagecontent = fields.get('newRestaurant')

                myNewRestaurant = Restaurant(name=messagecontent[0])
                session.add(myNewRestaurant)
                session.commit()

                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location', '/restaurants')
                self.end_headers()

            if self.path.endswith("/edit"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newName')


                # UPDATE
                laPath = self.path.split('/')
                print laPath  # ['', 'restaurants', '4', 'edit']
                laPathId = laPath[2]
                myRestaurant = session.query(Restaurant).filter_by(id=laPathId).one()
                if myRestaurant != []:
                    myRestaurant.name=messagecontent[0]
                    print myRestaurant.name
                    session.add(myRestaurant)
                    session.commit()

                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/restaurants')
                    self.end_headers()
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