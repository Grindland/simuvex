import simuvex

######################################
# open
######################################

class open(simuvex.SimProcedure): #pylint:disable=W0622
	def __init__(self): # pylint: disable=W0231
		# TODO: Symbolic fd
		path = self.arg(0)
		flags = self.arg(1)
		# TODO handle mode if flags == O_CREAT

		plugin = self.state['posix']

		# TODO handle errors and symbolic path
		fd = plugin.open(path, flags)
		self.ret(fd)