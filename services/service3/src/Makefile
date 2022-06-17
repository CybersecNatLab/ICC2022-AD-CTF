ALL=rpn
CFLAGS=-Wall -ggdb -Og -std=gnu11 -fstack-protector-all -Werror -pie -fpie -fpic -Wno-error=format-zero-length

rpn: rpn.c ANSI-color-codes.h cmd_tree.h monocypher.o
	$(CC) $(CFLAGS) -DNDEBUG -o rpn rpn.c monocypher.o
	cp rpn rpn_with_symbols
	strip --strip-all rpn

debug-builds: rpn.c ANSI-color-codes.h cmd_tree.h monocypher.o
	$(CC) -DDEV_DEBUG $(CFLAGS) -o rpn_with_debug rpn.c monocypher.o
	$(CC) -DDEV_DEBUG -DDEBUG_SET_VAR -DNO_SECCOMP $(CFLAGS) -fsanitize=address -o rpn_with_asan rpn.c monocypher.o

monocypher.o: monocypher.c
	$(CC) -c $(CFLAGS) monocypher.c

cmd_tree.h: cmd_tree.py
	./cmd_tree.py > cmd_tree.h

.PHONY: clean debug-builds

clean:
	rm -f rpn cmd_tree.h rpn_with_symbols monocypher.o
