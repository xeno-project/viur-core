# -*- coding: utf-8 -*-
from server.bones import baseBone
from server import utils
from google.appengine.ext import ndb
from server.utils import generateExpandoClass

class treeDirBone( baseBone ):
	def __init__( self, type, multiple=False, *args, **kwargs ):
		super( treeDirBone, self ).__init__( type=type, *args, **kwargs )
		self.type = type
		self.multiple = multiple

	
	def findPathInRepository( self, repository, path ):
		dbObj = utils.generateExpandoClass( self.type+"_repository" )
		repo = ndb.Key( urlsafe=repository ).get()
		for comp in path.split("/"):
			if not repo:
				return( None )
			if not comp:
				continue			
			repo = dbObj.query().filter( ndb.GenericProperty("parentdir" ) == repo.key.urlsafe() )\
					.filter( ndb.GenericProperty("name" ) == comp ).get()
		if not repo:
			return( None )
		else:
			return( repo )
	
		
	def fromClient( self, value ):
		self.value = []
		res = []
		if not value:
			return( "Invalid value entered" )
		if self.multiple:
			if not isinstance( value, list ):
				if value:
					if value.find("\n")!=-1:
						for val in value.replace("\r\n","\n").split("\n"):
							valstr = val
							if valstr and not self.canUse(  valstr  ):
								res.append(  valstr )
					else:
						valstr =  value
						if valstr and not self.canUse(  valstr ):
							res.append( valstr )
			else:
				for val in value:
					valstr =  val 
					if valstr and not self.canUse( valstr  ):
						res.append( valstr )
		else:
			valstr = value 
			if valstr and not self.canUse( valstr ):
				res.append( valstr )
		if len( res ) == 0:
			return( "No value entered" )
		if self.multiple:
			self.value = res
		else:
			self.value = res[0]
		return( None )
	
	def canUse( self, value ):
		try:
			repo, path = value.split("/",1)
		except:
			return("Invalid value")
		path = "/"+path
		repo = self.findPathInRepository( repo, path )
		if not repo:
			return( "Invalid path supplied" )
		return( None )
		
	def serialize(self, key ):
		if not self.value:
			return( {key:None } )
		return( {key: self.value } )
	
	def unserialize( self, name, expando ):
		super( treeDirBone, self ).unserialize( name, expando )
		if self.multiple and not self.value:
			self.value = []
