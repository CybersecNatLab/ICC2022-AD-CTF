ARG BASE_IMAGE=jammy-20220428

FROM ubuntu:${BASE_IMAGE} as nsjail_builder
ENV DEBIAN_FRONTEND noninteractive
RUN	apt-get -y update && apt-get install -y \
	autoconf \
	bison \
	flex \
	gcc \
	g++ \
	git \
	libprotobuf-dev \
	libnl-route-3-dev \
	libtool \
	make \
	pkg-config \
	protobuf-compiler \
	&& rm -rf /var/lib/apt/lists/*
RUN	cd / && \
	git clone https://github.com/google/nsjail.git && \
	cd /nsjail && \
	git checkout 3.1 && \
	make && \
	mv /nsjail/nsjail /bin && \
	rm -rf -- /nsjail

FROM ubuntu:${BASE_IMAGE}
ENV DEBIAN_FRONTEND noninteractive
RUN	apt-get -y update && apt-get install -y \
	libprotobuf-dev \
	libnl-route-3-dev \
	libtool \
	&& rm -rf /var/lib/apt/lists/*
COPY --from=nsjail_builder /bin/nsjail /bin/nsjail
RUN	mkdir -p /new_root /new_root/bin /new_root/flags && \
	mkdir /new_root/lib && \
	cp -r /usr/lib64 /new_root && \
	cp -r /lib/x86_64-linux-gnu /new_root/lib && \
	chown 0:0 -R /new_root && \
	chown 1337:1337 /new_root/flags && \
	chmod 700 /new_root/flags
EXPOSE 1982
COPY rpn /new_root/rpn
RUN chmod 555 /new_root/rpn
ENTRYPOINT [ "nsjail", \
	"-Ml", "--port", "1982", \
	"--user", "1337:1337", \
	"--group", "1337:1337", \
	"--disable_proc", \
	"--hostname", "pwn_jail", \
	"--time_limit", "120", \
	"--rlimit_cpu", "10", \
	"--rlimit_nproc", "20", \
	"--rlimit_as", "64", \
	"--rlimit_nofile", "16", \
	"--iface_no_lo", \
	"--rw", \
	"--chroot", "/new_root", \
	"--max_conns", "50", \
	"--", \
	"/rpn" ]
