from flask import Flask
from flask_restful import Api, Resource, reqparse
import hwLibEngine as HWL
import configEngine as CFG
from uuid import UUID
import os

# Utilites

def uid(value):
    # Check input string is UUID4 - raises exception if not
    uuid_obj = UUID(value, version=4)
    return str(uuid_obj)

def libErrHandler(func):
    # Decorator for engines requests
    def errDecorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (AttributeError, AssertionError):
            return 'Data not found', 404
        except CFG.AddError as e:
            return str(e), 400
    return errDecorator



# Startup

app = Flask(__name__)
api = Api(app)
libpath = os.path.dirname(os.path.abspath(__file__))
HWL.loadLib(libpath)
CFG.newConfig()

# Request parser

parser = reqparse.RequestParser()
parser.add_argument('active')
parser.add_argument('tag')
parser.add_argument('term')
parser.add_argument('newtag')
parser.add_argument('id')
parser.add_argument('addr')
parser.add_argument('unit', type=uid)
parser.add_argument('mode')
parser.add_argument('cmd')

# Library resources

class LibUnit(Resource):

    @libErrHandler
    def get(self, id=''):
        args = parser.parse_args()
        if id == '':
            if args['id'] is not None: id = args['id']
            elif args['tag'] is not None: id = HWL.idByTag(args['tag'])
        if id == '':
            return HWL.listUnits(), 200
        return HWL.getUnit(id), 200

    @libErrHandler
    def put(self, id=''):
        args = parser.parse_args()
        if id == '':
            if args['id'] is not None: id = args['id']
            elif args['tag'] is not None: id = HWL.idByTag(args['tag'])
        elif args['id'] is not None or args['tag'] is not None:
            return 'Bad request', 400
        if args['newtag'] is not None:
            return HWL.setUnitTag(id, args['newtag']), 201
        return 'Bad request', 400


class Term(Resource):

    @libErrHandler
    def get(self, id=''):
        args = parser.parse_args()
        if id == '':
            if args['term'] is not None: id = args['term']
        if id == '':
            return HWL.listTerms(), 200
        return HWL.getTerm(id), 200

class Lang(Resource):

    def get(self, val=''):
        if val == '':
            return HWL.langStat, 200
        if val == 'active':
            return HWL.lang, 200
        return 'Data not found', 404

    def put(self, val=''):
        args = parser.parse_args()
        task = args['active']
        if task == HWL.setLang(task):
            return task, 201
        return 'Bad request or language', 400

# Configuration resources

class Stat(Resource):

    @libErrHandler
    def get(self):
        return CFG.getStatus(), 200

    @libErrHandler
    def post(self):
        args = parser.parse_args()
        if args['cmd'] == 'save':
            CFG.saveConfig(libpath,'configtest.xml')
            return 'Save', 202
        if args['cmd'] == 'load':
            CFG.loadConfig(libpath,'configtest.xml')
            return 'Load', 202
        return 'Bad request', 400

class Res(Resource):

    @libErrHandler
    def get(self):
        return CFG.listResources(), 200

class Req(Resource):

    @libErrHandler
    def get(self):
        return CFG.listReqs(), 200

class Unit(Resource):

    @libErrHandler
    def get(self):
        args = parser.parse_args()
        unit = None
        mode = None
        if args['unit'] is not None: unit = args['unit']
        elif args['tag'] is not None: unit = CFG.idByTag(args['tag'])
        if args['mode'] == 'short': mode = CFG.DUMP_SHORT
        elif args['mode'] == 'full': mode = CFG.DUMP_FULL
        if unit is None:
            if mode is None: mode = CFG.DUMP_SHORT
            return CFG.listUnits(args['id'], mode), 200
        if mode is None: mode = CFG.DUMP_FULL
        return CFG.getUnit(unit, args['id'], mode), 200

    @libErrHandler
    def put(self):
        args = parser.parse_args()
        unit = None
        if args['unit'] is not None: unit = args['unit']
        elif args['tag'] is not None: unit = CFG.idByTag(args['tag'])
        if unit is None or args['newtag'] is None:
            return 'Bad request', 400
        return CFG.setUnitTag(unit, args['newtag']), 201
        
    @libErrHandler
    def post(self):
        args = parser.parse_args()
        unit = None
        if args['unit'] is not None: unit = args['unit']
        elif args['tag'] is not None: unit = CFG.idByTag(args['tag'])
        if unit is None or args['addr'] is None or args['id'] is None:
            return 'Bad request', 400
        return CFG.addUnit(args['id'], unit, args['addr']), 201

    @libErrHandler
    def delete(self):
        args = parser.parse_args()
        unit = None
        if args['unit'] is not None: unit = args['unit']
        elif args['tag'] is not None: unit = CFG.idByTag(args['tag'])
        if unit is None:
            return 'Bad request', 400
        return CFG.delUnit(unit), 204
        

# API    

api.add_resource(Lang, '/lang', '/lang/', '/lang/<string:val>')
api.add_resource(Term, '/hwlib/terms', '/hwlib/terms/', '/hwlib/terms/<string:id>')
api.add_resource(LibUnit, '/hwlib/units', '/hwlib/units/', '/hwlib/units/<string:id>')

api.add_resource(Stat, '/cfg/stat')
api.add_resource(Res, '/cfg/stat/res')
api.add_resource(Req, '/cfg/stat/req')
api.add_resource(Unit, '/cfg/units', '/cfg/units/')

if __name__ == '__main__':
    app.run(debug=True)
