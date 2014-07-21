import simuvex

######################################
# puts
######################################

class puts(simuvex.SimProcedure):
	def __init__(self): # pylint: disable=W0231,
		write = simuvex.SimProcedures['syscalls']['write']
		strlen = simuvex.SimProcedures['libc.so.6']['strlen']

		string = self.arg(0)
		length = self.inline_call(strlen, string).ret_expr
		self.inline_call(write, self.state.BVV(1, self.state.arch.bits), string, length)
		self.state['posix'].write(1, self.state.BVV(0x0a, 8), 1)

		# TODO: return values
		self.ret()