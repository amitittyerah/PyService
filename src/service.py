'''
    PyService
'''

import pycurl
import sys
import getopt
import json
import timeit

from xml.dom import minidom

'''
    Config variables
'''

debug = False
show_post_params = True
connection_timeout = 50
timeout = 80
fail_on_error = True
content_type = 'text/html'
charset = 'UTF-8'
sort_json_keys = True
json_indent = 6

'''
    Little utility class to handle color changes and text changes
'''


class Format:
    blue = "\033[94m"
    green = "\033[92m"
    red = "\033[91m"
    underline = "\033[4m"
    bold = "\033[1m"
    blink = "\033[5m"
    close = "\033[0m"


'''
    Little utility class to handle message output
'''


class Messages:
    def __init__(self):
        pass

    def print_new_group_start(self, name):
        print Format.bold + "\n\r\n\r\n\r\n\r------------------------------------\n\r\
STARTING GROUP : %s\n\r------------------------------------\n\r" % (name)

    def print_pycurl_error(self, errorstr):
        print Format.red + "!!!------\n\rACKACK\n\r------\n\rError :\
        \n\r%s\n\r------!!!!!" % (errorstr) + Format.close

    def print_curl_start(self, name, url):
        print Format.bold + Format.underline + Format.blue + str(name) + " called " + str(
            url) + " request" + Format.close + "\n\r"

    def print_curl_response_open(self):
        print Format.blink + "%s%s%s" % (Format.green, "\n\rStarting", Format.close)

    def print_curl_response_close(self):
        print Format.blink + "%s%s%s%s" % (Format.red, "Done", "\n\r", Format.close)

    def print_aborted_group(self, name):
        print "\n\r\n\rIgnoring group : %s\n\r\n\r" % name

    def print_json_output(self, json):
        print Format.underline + json + Format.close

    def print_process_exec_time(self, time):
        print "\n\rProcess took : %s%s%s seconds" % (Format.underline, str(time), Format.close)

    def print_services_called(self, count):
        print "Services called : %s%s%s" % (Format.underline, count, Format.close)

    def print_services_count(self, count):
        print "Total : %s%s%s" % (Format.underline, count, Format.close)

    def print_services_percent(self, percent):
        print "Success : %s%s%s%s" % (Format.underline, percent, "%", Format.close)

    def print_call_error(self, name):
        print Format.red + "!!!------\n\r\n\r------\n\rError :\
        \n\r%s\n\r------!!!!!" % name + Format.close

    def print_curl_params(self, str):
        post_list = str.split("&")
        print Format.blue + ">------------------------" + Format.close
        for x in post_list:
            print x
        print Format.blue + "<------------------------" + Format.close

    def print_services_status(self, services):
        for url, status in services.iteritems():
            print str(url) + " ---- " + str(status)


'''
    Writer class to handle output buffer storage
'''


class Writer:
    def __init__(self):
        self.buffer_stream = ''

    def write_to_buffer(self, buffer):
        self.buffer_stream += buffer

    def read_from_buffer(self):
        return self.buffer_stream

    def read_as_dict(self):
        return json.loads(self.buffer_stream)

    def read_as_json(self):
        json_stream = self.read_as_dict()
        return json.dumps(json_stream, sort_keys=sort_json_keys, indent=json_indent)


class ServiceCurl:
    '''
        ----------------------------------------
        Just a simple function for clean syntax
        ----------------------------------------
        Retrieves node value
        @node - the node to search in
        @str  - the index to search for
    '''

    def get_tag_child_data(self, node, str):
        try:
            return node.getElementsByTagName(str)[0].childNodes[0].data
        except:
            return ""

    '''
        ----------------------------------------
        Store responses
        ----------------------------------------
        Store responses from services in a dictionary to be used
        by other services. 
        @json_response - The response to parse
        @responses - the configuration from services.xml
    '''

    def store_responses(self, json_response, responses):
        for response in responses:
            if response['name'] in json_response:
                self.response_storage.update({response['var']: \
                                                  str(json_response[response['name']])})

    '''
        ----------------------------------------
        Clean Possible Variable (DEPRECATED)
        ----------------------------------------
        If a variable is actually a stand-in for a storage response, get the key.
    '''

    def clean_possible_variable(self, var):
        var = var.replace("${", "").replace("}$", "")
        return var

    '''
        ----------------------------------------
        Replace post string from response storage
        ----------------------------------------
        Replace stand-ins with values from the response storage
    '''

    def replace_post_string_from_response_storage(self, post_string):
        for key, value in self.response_storage.iteritems():
            post_string = post_string.replace("${" + str(key) + "}$", str(value))

        return post_string


    '''
        ----------------------------------------
        cURL the URL
        ----------------------------------------
        Outputs value
        @name - name of the service to test
        @url  - the url to call
        @post_string - the post parameters
    '''

    def start_curl_and_show_result(self, args):
        w = Writer()
        post_string = self.replace_post_string_from_response_storage(args['post_string'])
        curl_inst = pycurl.Curl() # start instance
        curl_inst.setopt(curl_inst.URL, str(args['url'])) # setup url to call
        curl_inst.setopt(curl_inst.POSTFIELDS, str(post_string)) # set the post fields
        curl_inst.setopt(curl_inst.SSL_VERIFYPEER, 0)
        curl_inst.setopt(curl_inst.SSL_VERIFYHOST, 0)
        curl_inst.setopt(curl_inst.CONNECTTIMEOUT, connection_timeout) # set connection timeout
        curl_inst.setopt(curl_inst.TIMEOUT, timeout) # timeout
        curl_inst.setopt(curl_inst.COOKIEFILE, '') # cookie?
        curl_inst.setopt(curl_inst.FAILONERROR, fail_on_error) # we want it to fail to pin point errors
        curl_inst.setopt(curl_inst.HTTPHEADER, ['Accept: %s' % (content_type), 'Accept-Charset: %s' % (charset)])
        curl_inst.setopt(curl_inst.VERBOSE, debug)
        curl_inst.setopt(curl_inst.WRITEFUNCTION, w.write_to_buffer)
        
        if args['ssl_ca'] and args['ssl_cert'] and args['ssl_key']:
            curl_inst.setopt(curl_inst.CAINFO, args['ssl_ca'])
            curl_inst.setopt(curl_inst.SSLCERT, args['ssl_cert'])
            curl_inst.setopt(curl_inst.SSLKEY, args['ssl_key'])
            
        
        self.m.print_curl_start(args['name'], args['url'])
        self.service_statuses.update({args['url']: Format.green + "Success" + Format.close})
        if show_post_params:
            self.m.print_curl_params(post_string)
        try:
            self.m.print_curl_response_open()
            curl_inst.perform() # write to buffer
            json_response = w.read_as_json()

            self.store_responses(w.read_as_dict(), args['responses'])
            self.m.print_json_output(json_response)
            self.m.print_curl_response_close()
        except Exception, error:
            errorstr = error
            print "BUFFER : " + w.read_from_buffer()
            self.service_statuses.update({args['url']: Format.red + "Fail" + Format.close})
            self.m.print_pycurl_error(errorstr)


    '''
        ----------------------------------------
        Call the services
        ----------------------------------------
        @service_dict - dictionary of services to call
    '''

    def call_services(self, service_dict):
        called = 0
        for service in service_dict:
            try:
                self.start_curl_and_show_result(service)
                called += 1

            except Exception, e:
                self.m.print_call_error(service['name'] + " : " + str(e))
                pass
        return called

    '''
        ----------------------------------------
        Replace URL String with Arguments Passed
        ----------------------------------------
        Used to replace ${}$ variables from the URL with argument values
    '''

    def replace_url_string_with_args(self, url, temp):
        return url.replace("${temp}$", temp)


    '''
        ----------------------------------------
        INIT
        ----------------------------------------
        @group_specific - the specific group to test
    '''

    def __init__(self, user_args):
        time_started = timeit.default_timer()
        services_count = 0
        services_failed = 0
        service_dict = []
        self.response_storage = {}
        self.service_statuses = {}
        self.m = Messages()
        # parse the xml
        xmldoc = minidom.parse('services.xml')

        # for each service outlined there, grab the required values
        for group in xmldoc.getElementsByTagName('group'):
            ssl_key     = False
            ssl_cert    = False
            ssl_ca      = False

            group_name = str(group.getAttributeNode('name').nodeValue)
            base_url = str(group.getAttributeNode('base').nodeValue)

            is_disabled = str(group.getAttributeNode('disabled').nodeValue) \
                if (group.getAttributeNode('disabled')) else False
            try:
                ssl_ca      = str(group.getAttributeNode('ssl_ca').nodeValue)
                ssl_cert    = str(group.getAttributeNode('ssl_cert').nodeValue)
                ssl_key     = str(group.getAttributeNode('ssl_key').nodeValue)
            except:
                print "No ssl info for %s" % (group_name)
        
            
            
            # if group specified, check if group is in choice
            if (not user_args['group'] and not is_disabled )or (user_args['group'] and \
                                                  str(group_name).lower() in user_args['group']):
            
                for service in group.getElementsByTagName('service'):
                    post_string = ""
                    responses = []
                    name = str(service.getAttributeNode('name').nodeValue)
                    # if service specified, check if service in choice
                    if not user_args['service'] or (user_args['service'] and \
                                                            str(name).lower() in user_args['service']):
                        services_count += 1
                        url = base_url + str(service.getAttributeNode('url').nodeValue)
                        # for each parameter in parameters, grab and create the post string
                        for parameter in service.getElementsByTagName('parameter'):
                            p_name = self.get_tag_child_data(parameter, 'name')
                            p_value = self.get_tag_child_data(parameter, 'value')
                            if len(p_value) > 0 and len(p_name) > 0:
                                post_string += "%s=%s&" % (str(p_name), str(p_value))
                            else:
                                self.m.print_call_error(name)
                                break
                        for response in service.getElementsByTagName('response'):
                            response_var_name = response.getAttributeNode('name').nodeValue
                            response_param_name = self.get_tag_child_data(response, 'name')
                            responses.append({'var': str(response_var_name), 'name': str(response_param_name)})
                        if len(name) > 0 and len(url) > 0:
                            if user_args['temp']:
                                url = self.replace_url_string_with_args(url, user_args['temp'])
                            service_dict.append({"name": name, "url": url, 
                                                 "post_string": post_string, 
                                                 "responses": responses,
                                                 "ssl_ca" : ssl_ca,
                                                 "ssl_cert" : ssl_cert,
                                                 "ssl_key" : ssl_key
                                                })

            else:
                self.m.print_aborted_group(group_name)

        services_successfully_called = self.call_services(service_dict)
        time_ended = timeit.default_timer()

        # Outputs
        self.m.print_process_exec_time(str(time_ended - time_started))
        self.m.print_services_count(services_count)
        self.m.print_services_called(services_successfully_called)
        if services_count > 0:
            self.m.print_services_percent(float(services_successfully_called * 100 / services_count))
        self.m.print_services_status(self.service_statuses)


def check_args(args):
    group = False
    service_to_call = False
    temp = False
    try:
        opts, args = getopt.getopt(args, "g:s:t:")
    except getopt.GetoptError, error:
        print "Empty service name"
        sys.exit()

    for opt, arg in opts:
        if opt == "-g": # specific group name
            group = str(arg).split(",")
        elif opt == "-s": # specific service name
            service_to_call = str(arg).split(",")
        elif opt == "-t": # replace the temporary variable
            temp = str(arg)
    return {"group": group, "service": service_to_call, "temp": temp}


if __name__ == "__main__":
    args = sys.argv[1:]
    group_specific = check_args(args)
    ServiceCurl(group_specific)

