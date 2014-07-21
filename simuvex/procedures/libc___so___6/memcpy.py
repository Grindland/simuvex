import simuvex

import logging
l = logging.getLogger("simuvex.procedures.libc.memcpy")

class memcpy(simuvex.SimProcedure):
	def __init__(self): # pylint: disable=W0231,
		dst_addr = self.arg(0)
		src_addr = self.arg(1)
		limit = self.arg(2)

		if not limit.symbolic:
			conditional_size = self.state.any(limit)
		else:
			max_memcpy_size = self.state['libc'].max_buffer_size
			conditional_size = max(self.state.min(limit), min(self.state.max(limit), max_memcpy_size))

		l.debug("Memcpy running with conditional_size %d", conditional_size)

		if conditional_size > 0:
			src_mem = self.state.mem_expr(src_addr, conditional_size, endness='Iend_BE')
			self.state.store_mem(dst_addr, src_mem, symbolic_length=limit, endness='Iend_BE')

			self.add_refs(simuvex.SimMemRead(self.addr, self.stmt_from, src_addr, src_mem, conditional_size))
			self.add_refs(simuvex.SimMemWrite(self.addr, self.stmt_from, dst_addr, src_mem, conditional_size))

		self.ret(dst_addr)