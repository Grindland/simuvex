from ..s_state import SimStatePlugin
from ..s_file import SimFile
from ..s_pcap import PCAP
from ..s_errors import SimMergeError

import copy

import logging
l = logging.getLogger('simuvex.procedures.syscalls')

max_fds = 8192

class SimStateSystem(SimStatePlugin):
	#__slots__ = [ 'maximum_symbolic_syscalls', 'files', 'max_length' ]

	def __init__(self, initialize=True, files=None, sockets=None, pcap_backer=None):
		SimStatePlugin.__init__(self)
		self.maximum_symbolic_syscalls = 255
		self.files = { } if files is None else files
		self.max_length = 2 ** 16
		self.sockets = {} if sockets is None else sockets
		self.pcap = None if pcap_backer is None else pcap_backer
		self.pflag = 0 if self.pcap is None else 1

		if initialize:
			l.debug("Initializing files...")
			self.open("stdin", "r") # stdin
			self.open("stdout", "w") # stdout
			self.open("stderr", "w") # stderr
			#TODO: Fix the temp hack of a tuple - used to determine traffic from us vs traffic to us
			if pcap_backer is not None:
				self.pcap = PCAP(pcap_backer, ('127.0.0.1', 8888))
		else:
			l.debug("Not initializing files...")

	#to keep track of sockets
	def add_socket(self, fd):
		self.sockets[fd] = self.files[fd]

	#back a file with a pcap
	def backme(self, fd):
		#import ipdb;ipdb.set_trace()
		if self.pcap is not None:
			self.get_file(fd).bind_file(self.pcap)

	def set_state(self, state):
		SimStatePlugin.set_state(self, state)
		for f in self.files.itervalues():
			f.set_state(state)

	def open(self, name, mode, preferred_fd=None):
		# TODO: speed this up
		fd = None
		if preferred_fd is not None:
			if preferred_fd in self.files:
				raise Exception("A file with fd %d already exists.", preferred_fd)
			else:
				fd = preferred_fd
		else:
			for fd_ in xrange(0, 8192):
				if fd_ not in self.files:
					fd = fd_
					break
		if fd is None:
			raise Exception("File descriptors are used up.")
		self.files[fd] = SimFile(fd, name, mode)
		if self.state is not None:
			self.files[fd].set_state(self.state)
		return fd

	def read(self, fd, length, pos=None):
		# TODO: error handling
		# TODO: symbolic support
		fd = self.state.make_concrete_int(fd)
		expr, constraints = self.get_file(fd).read(length, pos)
		self.state.add_constraints(*constraints)
		return expr

	def write(self, fd, content, length, pos=None):
		# TODO: error handling
		# TODO: symbolic support
		fd = self.state.make_concrete_int(fd)
		length = self.state.make_concrete_int(length)
		return self.get_file(fd).write(content, length, pos)

	def close(self, fd):
		# TODO: error handling
		# TODO: symbolic support?
		fd = self.state.make_concrete_int(fd)
		del self.files[fd]

	def seek(self, fd, seek):
		# TODO: symbolic support?
		fd = self.state.make_concrete_int(fd)
		self.get_file(fd).seek(seek)

	def copy(self):
		sockets = {}
		files = { fd:copy.copy(f) for fd,f in self.files.iteritems() }
		for f in self.files:
			if f in self.sockets:
				sockets[f] = files[f]
		return SimStateSystem(initialize=False, files=files, sockets=sockets, pcap_backer=self.pcap)

	def merge(self, others, merge_flag, flag_values):
		if len(set(frozenset(o.files.keys()) for o in [ self ] + others)) != 1:
			raise SimMergeError("Unable to merge SimStateSystem with different sets of open files.")

		all_constraints = [ ]

		for fd in self.files:
			constraints = self.get_file(fd).merge([ o.files[fd] for o in others ], merge_flag, flag_values)
			all_constraints += constraints

		return all_constraints

	def dumps(self, fd):
		return self.state.se.any_str(self.get_file(fd).all_bytes())

	def dump(self, fd, filename):
		open(filename, "w").write(self.dumps(fd))

	def get_file(self, fd):
		if fd not in self.files:
			l.warning("Accessing non-existing file with fd %d. Creating a new file.", fd)
			self.open("tmp_%d" % fd, "wr", preferred_fd=fd)
		return self.files[fd]

SimStatePlugin.register_default('posix', SimStateSystem)