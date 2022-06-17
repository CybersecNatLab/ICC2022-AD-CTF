#include <bits/time.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdbool.h>
#include <ctype.h>
#include <string.h>
#include <assert.h>
#include <stdint.h>
#include <inttypes.h>
#include <time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/file.h>
#include <fcntl.h>
#include <linux/seccomp.h>
#include <sys/prctl.h>
#include <sys/random.h>
#ifdef NO_COLORS
#include "no-ANSI-color-codes.h"
#else
#include "ANSI-color-codes.h"
#endif
#include "monocypher.h"

#define MAX_LINE_LENGTH 4096
#define MAX_TOKENS MAX_LINE_LENGTH
#define MAX_STR_ID_LEN 32 /* see also print_stack and cmd_vars */
#define N_VARS_PER_STORE 64
#define MAX_STACK_ELEMENTS 16
#define MAX_VAR_IN_STORE_PER_SIGNER 8 /* checker + 7 teams -> 64 slots (*2 stores) -> 128 slots */
#ifdef DEV_DEBUG
#define FLAG_STORE_FILENAME "/tmp/flagstore"
#else
#define FLAG_STORE_FILENAME "/flags/flagstore"
#endif

#define EC_INVALID_OPERAND 0x3813f3cee5040b5
#define EC_MISSING_OPERAND 0x3813f36cee5040b3
#define EC_MISSING_ARGUMENT 0x3813f3c6ee5040b3
#define EC_ARGUMENT_MUST_BE_INT 0xfff6bfb7fc1841db
#define EC_OPERAND_MUST_BE_INT 0xfff6bfb7cf1841db
#define EC_OPERAND_MUST_BE_NON_NEG 0x5640e01698ee6515
#define EC_THERE_IS_NOTHING 0x31c46917d70649d2
#define EC_STACK_IS_FULL 0x1e5b292901c995c9
#define EC_UNCLOSED_STR_LITERAL 0x27c0f88ad329c6b7
#define EC_UNRECOGNIZED_ESCAPE 0x863baa576a944788
#define EC_IDENT_TOO_LONG 0x7ec829d4b89fdbf4
#define EC_STR_LITERAL_TOO_LONG 0x7ec289d4b89fdbf4
#define EC_INCOMPLETE_STR_LITERAL 0x5b2c448fcc5cac7e
#define EC_STACK_IS_EMPTY 0x440724385fb22e
#define EC_ONLY_IN_DEBUG 0x9f79cbb5ab266b66
#define EC_TOO_FEW_OPERANDS 0x24cdab500abbfbe0
#define EC_TOP_MUST_BE_ID 0xf9eaea4a29a3a1d1
#define EC_TOP_MUST_BE_INT 0xf9eaae4a29a3a1d1
#define EC_TOP_MUST_BE_INTS 0xf9eaae4a293aa1d1
#define EC_TOP_MUST_BE_STR 0x9feaae4a29a3a1d1
#define EC_UNDEF_VAR 0x182a805ee937b4f5
#define EC_2ND_MUST_BE_STR_OR_INT 0xba2689aea5af9134
#define EC_2ND_MUST_BE_INT 0xba2689aea5af9314
#define EC_DEBUG_ONLY_IN_DEV 0x18f4ff408b014d09
#define EC_INVALID_CHAR_IN_KW 0xd480aff582d340a9
#define EC_INVALID_KEYWORD 0x817409fc57f4a1b0
#define EC_INT_LITERAL_TOO_LONG 0xb410eb3da2f7306
#define EC_INVALID_CHAR_IN_INT_LITERAL 0xc619e22ee6d38fc0
#define EC_INVALID_INT_LITERAL 0xc619e2e2e6d38fc0
#define EC_UNEXPECTED_INPUT 0x935dbd84cb78471e
#define EC_TOO_MANY_TOKENS 0x78ca6bfa18abe98
#define EC_INTERNAL_PARSER_ERROR 0x78ac6bfa18abe98
#define EC_NO_ARGS_ON_CMDLINE 0x13d6334f64ebd128
#define EC_DUP_TAKES_ONLY_AN_OPTIONAL_ARGUMENT 0x37fdaa73bbd5eb4b
#define EC_ARGUMENT_TOO_BIG 0x3f7daa73bbd5eb4b
#define EC_TIME_OUT_OF_RANGE 0x3f7daa37bbd5eb4b
#define EC_BAD_SIGNER_TAG 0x3f7dfa37bbd5eb4b
#define EC_CORRUPTED_STORE 0x3f7dfa37bb5deb4b

static unsigned int signer = -1;

void print_error_0p(char *fmt)
{
	printf(BRED "%s." reset "\n", fmt);
}

void print_error_1p(char *fmt, char *p1)
{
	printf(BRED);
	printf(fmt, p1);
	printf(reset);
}

void print_error(uint64_t err_code)
{
	char *s;
	switch(err_code) {
	case EC_INVALID_OPERAND: s = "Invalid operand"; break;
	case EC_MISSING_OPERAND: s = "Missing operand"; break;
	case EC_MISSING_ARGUMENT: s = "Missing argument"; break;
	case EC_ARGUMENT_MUST_BE_INT: s = "The argument must be an integer"; break;
	case EC_ARGUMENT_TOO_BIG: s = "The argument is too big"; break;
	case EC_OPERAND_MUST_BE_INT: s = "The operand must be an integer"; break;
	case EC_OPERAND_MUST_BE_NON_NEG: s = "Bad operand; the index must be non-negative"; break;
	case EC_DUP_TAKES_ONLY_AN_OPTIONAL_ARGUMENT: s = "Dup takes only an optional (integer) argument"; break;
	case EC_THERE_IS_NOTHING: s = "These is nothing there"; break;
	case EC_STACK_IS_FULL: s = "Stack is full"; break;
	case EC_STACK_IS_EMPTY: s = "Stack is empty"; break;
	case EC_ONLY_IN_DEBUG: s = "This command is only available in debug mode"; break;
	case EC_TOO_FEW_OPERANDS: s = "Too few operands on the stack"; break;
	case EC_TOP_MUST_BE_ID: s = "The top element must be an identifier"; break;
	case EC_TOP_MUST_BE_INT: s = "The top element must be an integer"; break;
	case EC_TOP_MUST_BE_INTS: s = "The top elements must be integers"; break;
	case EC_TOP_MUST_BE_STR: s = "The top element must be a string"; break;
	case EC_UNDEF_VAR: s = "Undefined variable"; break;
	case EC_2ND_MUST_BE_STR_OR_INT: s = "The 2nd element must be an integer or a string"; break;
	case EC_2ND_MUST_BE_INT: s = "The 2nd element must be an integer"; break;
	case EC_DEBUG_ONLY_IN_DEV: s = "Debug mode can be changed in development-mode only"; break;
	case EC_TOO_MANY_TOKENS: s = "Too many tokens; please enter a value/identifier at a time"; break;
	case EC_INTERNAL_PARSER_ERROR: s = "Internal parser error"; break;
	case EC_NO_ARGS_ON_CMDLINE: s = "This operation takes no arguments from the command-line"; break;
	case EC_BAD_SIGNER_TAG: s = "Internal server error: bad signer-tag."; break;
	case EC_CORRUPTED_STORE: s = "Internal server error: corrupted store."; break;
	case EC_INVALID_KEYWORD: s = "Invalid keyword."; break;
	default:
		assert(0);
		s = "*** UNDEFINED ERROR CONDITION ***";
	}
	print_error_0p(s);
}

void print_error_1(uint64_t err_code, char *p1)
{
	char *s;
	switch(err_code) {
	case EC_UNCLOSED_STR_LITERAL: s = "Unclosed string literal: %s"; break;
	case EC_UNRECOGNIZED_ESCAPE: s = "Unrecognized escape in string literal: %s"; break;
	case EC_STR_LITERAL_TOO_LONG: s = "String literal too long: %s"; break;
	case EC_INT_LITERAL_TOO_LONG: s = "Integer literal too long: %s"; break;
	case EC_IDENT_TOO_LONG: s = "Identifier too long: %s"; break;
	case EC_INVALID_CHAR_IN_KW: s = "Invalid character in keyword: %s"; break;
	case EC_INVALID_KEYWORD: s = "Invalid keyword: %s"; break;
	case EC_INVALID_CHAR_IN_INT_LITERAL: s = "Invalid character in integer literal: %s"; break;
	case EC_INVALID_INT_LITERAL: s = "Invalid integer literal: %s"; break;
	case EC_UNEXPECTED_INPUT: s = "Unexpected input: %s"; break;
	case EC_TIME_OUT_OF_RANGE: s = "Unix-time out of range: %sd"; break;
	default:
		assert(0);
		s = "*** UNDEFINED ERROR CONDITION ***";
	}
	print_error_1p(s, p1);
}

static int fd_store;

typedef void (*cmd_func_t)();

typedef struct {
	enum tok_type {
		TOK_NONE = 0,
		TOK_KEYWORD = 1,
		TOK_IDENT = 2,
		TOK_NUMBER = 3,
		TOK_STRING = 4,
	} type;
	char *lexeme;
	char str_id_value[MAX_STR_ID_LEN+1];
	int64_t int_value;
	cmd_func_t kw_function;
} token;

#define VT_EMPTY      0
#define VT_NUMBER     0xa005305a // 0b6bc11a
#define VT_STRING     0x894aba46 // 3f0646b1
#define VT_IDENTIFIER 0x74564d83 // 9675d691

typedef struct {
	unsigned int type;
	unsigned int signer;
	union {
		char str_id_value[MAX_STR_ID_LEN];
		int64_t int_value;
	};
} value_t;

static struct {
	char	int_literal_conversion_buffer[64];
	char	store1_var_names[N_VARS_PER_STORE][MAX_STR_ID_LEN];
	int	padding1;
	int	padding2;
	char	store2_var_names[N_VARS_PER_STORE][MAX_STR_ID_LEN];
} b0;
static uint64_t	store1_timestamps[N_VARS_PER_STORE];
static uint64_t	store2_timestamps[N_VARS_PER_STORE];
static struct {
	value_t pad0;
	value_t	store1_values[N_VARS_PER_STORE];
	value_t pad1;
	value_t pad2;
	value_t pad3;
	value_t	stack[MAX_STACK_ELEMENTS];
	value_t pad4;
	value_t buffer_for_time2str;
	value_t	store2_values[N_VARS_PER_STORE];
} b1;
static int stack_len;

enum {
	print_in_dec = 1,
	print_in_hex = 2,
	print_in_oct = 3,
	debug_mode   = 16
};

static struct {
	char safe_area_for_underflow_in_parse_str_buf[MAX_LINE_LENGTH];
	int mode_flags;
	int some_padding1;
	char parse_str_buf[MAX_LINE_LENGTH+1];
	int some_padding2;
} dm = { .mode_flags = print_in_dec };

#if 0
void print_up_to_16(char *s)
{
	int len=0;
	for(;*s;++s,++len) {
		if (len==16) {
			printf("...");
			return;
		}
		putchar(*s);
	}
}
#endif

void print_stack()
{
#ifdef DEV_DEBUG
	printf("stack_len=%d\n", stack_len);
#endif
	if (stack_len==0) {
		printf("The value stack is empty.\n");
		return;
	}
	const int print_base = dm.mode_flags & 3;
	printf("Current base: ");
	switch (print_base) {
	case print_in_dec: printf("Dec\n"); break;
	case print_in_hex: printf("Hex\n"); break;
	case print_in_oct: printf("Oct\n"); break;
	}
	for(int i = MAX_STACK_ELEMENTS-1; i>=0; --i) {
		value_t *s = b1.stack + i;
		if (s->type==VT_EMPTY)
			continue;
		printf(BWHT "[%2d] ", i);
		switch (s->type) {
		case VT_NUMBER:
			{
				int64_t value = s->int_value == 0x0ddba11 ? (int64_t)&s->int_value : s->int_value;
				switch (print_base) {
				case print_in_dec: printf(MAG "%" PRId64, value); break;
				case print_in_hex: printf(MAG "%" PRIx64, value); break;
				case print_in_oct: printf(MAG "%" PRIo64, value); break;
				}
				break;
			}
		case VT_STRING:
			printf(YEL "\"%.32s\"", s->str_id_value);
			/* printf(YEL "\""); */
			/* print_up_to_16(s->str_id_value); */
			/* putchar('\"'); */
			break;
		case VT_IDENTIFIER:
			printf(GRN "%.32s", s->str_id_value);
			/* printf(GRN); */
			/* print_up_to_16(s->str_id_value); */
			break;
		case VT_EMPTY:
			/* nop */
		default: ; // nop
			/* printf(ERROR "Corrupted value-type %ld (this shouldn't happen)\n" reset, s->type); */
			//assert(0);
		}
		printf(reset "\n");
	}
}

void push_ident(token *t)
{
	if (stack_len == MAX_STACK_ELEMENTS) {
		print_error(EC_STACK_IS_FULL);
		++stack_len;
		return;
	}
	memmove(b1.stack+1, b1.stack, sizeof(b1.stack)-sizeof(*b1.stack));
	b1.stack[0].type = VT_IDENTIFIER;
	memset(b1.stack[0].str_id_value, 0, sizeof(b1.stack[0].str_id_value));
	strncpy(b1.stack[0].str_id_value, t->lexeme, MAX_STR_ID_LEN);
	++stack_len;
}

void push_int(token *t)
{
	if (++stack_len > MAX_STACK_ELEMENTS) {
		print_error(EC_STACK_IS_FULL);
		stack_len = MAX_STACK_ELEMENTS;
		return;
	}
	memmove(b1.stack+1, b1.stack, sizeof(b1.stack)-sizeof(*b1.stack));
	b1.stack[0].type = VT_NUMBER;
	memset(b1.stack[0].str_id_value, 255, sizeof(b1.stack[0].str_id_value));
	b1.stack[0].int_value = t->int_value;
}

void push_string(token *t)
{
	if (++stack_len > MAX_STACK_ELEMENTS) {
		print_error(EC_STACK_IS_FULL);
		stack_len = MAX_STACK_ELEMENTS;
		return;
	}
	memmove(b1.stack+1, b1.stack, sizeof(b1.stack)-sizeof(*b1.stack));
	memset(b1.stack[0].str_id_value, 0, sizeof(b1.stack[0].str_id_value));
	b1.stack[0].type = VT_STRING;
	strncpy(b1.stack[0].str_id_value, t->str_id_value, MAX_STR_ID_LEN);
}

static bool dev_mode;
static token tokens[MAX_TOKENS];
static int n_tokens;

bool there_are_no_spurious_args()
{
	if (n_tokens == 1)
		return true;
	print_error(EC_NO_ARGS_ON_CMDLINE);
	return false;
}

uint64_t get_time()
{
	struct timespec t;
	if (clock_gettime(CLOCK_MONOTONIC_RAW, &t)) {
		perror("clock_gettime");
		exit(EXIT_FAILURE);
	}
	return (uint64_t)t.tv_sec*1000000 + (uint64_t)t.tv_nsec/1000;
}

static char *parse_string_literal(char *l)
{
	char *out = dm.parse_str_buf;
	char *in = l;
	char terminator = *in++;
	bool escape = false;
	int len = 0;
	for(;;) {
		if (!*in) {
			print_error_1(EC_UNCLOSED_STR_LITERAL, l);
			return 0;
		}
		if (escape) {
			--out;
			switch (*in++) {
			case 'n': *out++ = '\n'; break;
			case 'r': *out++ = '\r'; break;
			case 't': *out++ = '\t'; break;
			case '\'': *out++ = '\''; break;
			case '\"': *out++ = '\"'; break;
			case '\\': break;
			default:
				print_error_1(EC_UNRECOGNIZED_ESCAPE, l);
				return 0;
			}
			escape = false;
			continue;
		}
		if (*in==terminator) {
#ifdef DEV_DEBUG
			printf("out=%p parse_str_buf=%p &mode_flags=%p mode_flags=%x\n", out, dm.parse_str_buf, &dm.mode_flags, dm.mode_flags);
#endif
			*out = 0;
			tokens[n_tokens].type = TOK_STRING;
			tokens[n_tokens].lexeme = l;
			strcpy(tokens[n_tokens].str_id_value, dm.parse_str_buf);
			++n_tokens;
			++in;
			if (*in)
				*in++ = 0;
			return in;
		}
		if (++len > MAX_STR_ID_LEN) {
			print_error_1(EC_STR_LITERAL_TOO_LONG, l);
			return 0;
		}
		if ( (*out++ = *in++) == '\\' ) {
			escape = true;
			if (!*in) {
				print_error_1(EC_INCOMPLETE_STR_LITERAL, l);
				return 0;
			}
			if (*in=='\\') --out;
		}
	}
}

#if 0
static void print_tokens()
{
	printf("n_tokens=%d\n", n_tokens);
	token *t = tokens;
	for(int a=0; a<n_tokens; ++a, ++t) {
		printf(YEL);
		switch(t->type) {
		case TOK_KEYWORD:
			printf("TOK_KEYWORD " reset);
			break;
		case TOK_IDENT:
			printf("TOK_IDENT   " reset);
			break;
		case TOK_NUMBER:
			printf("TOK_NUMBER  " reset);
			break;
		case TOK_STRING:
			printf("TOK_STRING  " reset);
			break;
		default: assert(false);
		}
		printf(reset);
		printf(" lexeme=" BWHT "%s" reset, t->lexeme);
		switch(t->type) {
		case TOK_KEYWORD:
			printf(" hash=" MAG "%" PRId64 reset, t->int_value);
			break;
		case TOK_IDENT:
			break;
		case TOK_NUMBER:
			printf(" int_value=" MAG "%" PRId64 reset, t->int_value);
			break;
		case TOK_STRING:
			printf(" str_value=" MAG "%s" reset, t->str_id_value);
			break;
		default: assert(false);
		}
		putchar('\n');
	}
}
#endif

static void cmd_ver()
{
	printf("bb52963df0c359f3\n");
	printf("22adcea545341e45\n");
	printf("4b91685c14458e3d\n");
	printf("982059cf01a70efb\n");
}

static void cmd_next_base()
{
	if (!there_are_no_spurious_args())
		return;
	++dm.mode_flags;
	dm.mode_flags &= 31;
	if ((dm.mode_flags&3)==0)
		++dm.mode_flags;
}

static void cmd_dec()
{
	if (!there_are_no_spurious_args())
		return;
	dm.mode_flags = print_in_dec;
}

static void cmd_hex()
{
	if (!there_are_no_spurious_args())
		return;
	dm.mode_flags = print_in_hex;
}

static void cmd_oct()
{
	if (!there_are_no_spurious_args())
		return;
	dm.mode_flags = print_in_oct;
}

static void cmd_time()
{
	if (!there_are_no_spurious_args())
		return;
	if ((stack_len+1) > MAX_STACK_ELEMENTS) {
		print_error(EC_STACK_IS_FULL);
		return;
	}
	++stack_len;
	memmove(b1.stack+1, b1.stack, sizeof(b1.stack)-sizeof(*b1.stack));
	b1.stack[0].type = VT_NUMBER;
	b1.stack[0].int_value = time(0);
}

static void cmd_random()
{
	if (!there_are_no_spurious_args())
		return;
	if ((stack_len+1) > MAX_STACK_ELEMENTS) {
		print_error(EC_STACK_IS_FULL);
		return;
	}
	++stack_len;
	memmove(b1.stack+1, b1.stack, sizeof(b1.stack)-sizeof(*b1.stack));
	b1.stack[0].type = VT_NUMBER;
	b1.stack[0].int_value = (((uint64_t)&b1.store1_values) >> 12) ^ random();
		// the first call to random is always 1804289383
}

static void cmd_dup()
{
	if (stack_len==0) {
		print_error(EC_STACK_IS_EMPTY);
		return;
	}
	uint64_t n = 1;
	if (n_tokens > 2) {
		print_error(EC_DUP_TAKES_ONLY_AN_OPTIONAL_ARGUMENT);
		return;
	}
	if (n_tokens == 2) {
		if (tokens[1].type != TOK_NUMBER) {
			print_error(EC_ARGUMENT_MUST_BE_INT);
			return;
		}
		n = tokens[1].int_value;
		if (n >= MAX_STACK_ELEMENTS) {
			print_error(EC_ARGUMENT_TOO_BIG);
			return;
		}
	}
	stack_len += n;
	if (stack_len > MAX_STACK_ELEMENTS) {
		print_error(EC_STACK_IS_FULL);
		stack_len -= n;
		return;
	}
	while (n-- > 0) {
		memmove(b1.stack+1, b1.stack, sizeof(b1.stack)-sizeof(*b1.stack));
		b1.stack[0] = b1.stack[1];
	}
}

static void cmd_peek()
{
	if (!there_are_no_spurious_args())
		return;
	if (stack_len<1 || b1.stack[0].type!=VT_NUMBER) {
		return;
	}
	b1.stack[0].type = VT_NUMBER;
	b1.stack[0].int_value = *((int64_t *)b1.stack[0].int_value);
}

static void cmd_swap()
{
	if (stack_len<2) {
error:
		print_error(EC_TOO_FEW_OPERANDS);
		return;
	}
	if (n_tokens > 2) {
		print_error(EC_NO_ARGS_ON_CMDLINE);
		return;
	}
	int64_t other_index = 1;
	if (n_tokens == 2 && tokens[1].type == TOK_NUMBER)
		other_index = tokens[1].int_value;
	if (other_index == 0 || other_index >= stack_len)
		goto error;
	const uint64_t t = b1.stack[other_index].type;
	if (t != VT_NUMBER && t != VT_STRING && t != VT_IDENTIFIER)
		goto error;
	value_t tmp = b1.stack[0];
	b1.stack[0] = b1.stack[other_index];
	if (other_index < 0)
		goto error;
	b1.stack[other_index] = tmp;
}

static void cmd_todohxd()
{
	if (!there_are_no_spurious_args())
		return;
	if (stack_len<2 || b1.stack[0].type!=VT_NUMBER || b1.stack[1].type!=VT_NUMBER) {
		return;
	}
	char *buf = (char *)b1.stack[0].int_value;
	char *end_buf = buf + b1.stack[1].int_value;
	for(; buf < end_buf ; buf += sizeof(void *)) {
		printf(CYN "%p" WHT " | ", buf);
		unsigned char *pc;
		pc = (unsigned char *)buf;
		int b;
		printf(YEL);
		for(b=0; b<sizeof(void*); ++b) {
			unsigned char c = pc[b];
			printf("%02x ", (unsigned int)c); \
		}
		printf(WHT " | "); \
		for(b=0; b<sizeof(void*); ++b) {
			unsigned char c = pc[b];
			putchar((c>=' ' && c<127) ? c : '.');
		}
		printf(" | "); \
		printf(WHT "\n"); \
	}
}

static void cmd_clear()
{
	if (!there_are_no_spurious_args())
		return;
	for(int i = 0; i<MAX_STACK_ELEMENTS; ++i)
		b1.stack[i].type = VT_EMPTY;
	stack_len = 0;
}

int64_t operand1, operand2;

extern bool ok_for_arithmetic();

static void cmd_add()
{
	if (ok_for_arithmetic())
		b1.stack[0].int_value = operand1 + operand2;
}

static void cmd_div()
{
	if (ok_for_arithmetic()) {
		if (operand2==0) {
			b1.stack[0].type = VT_IDENTIFIER;
			strcpy(b1.stack[0].str_id_value, "Division_by_zero");
		} else
			b1.stack[0].int_value = operand1 / operand2;
	}
}

static void cmd_and()
{
	if (ok_for_arithmetic())
		b1.stack[0].int_value = operand1 & operand2;
}

static void cmd_sub()
{
	if (ok_for_arithmetic())
		b1.stack[0].int_value = operand1 - operand2;
}

static void cmd_quit()
{
	if (!there_are_no_spurious_args())
		return;
	printf("So long and thanks for all the fish\n");
	exit(EXIT_SUCCESS);
}

static void cmd_drop()
{
	if (!there_are_no_spurious_args())
		return;
	if (stack_len==0) {
		print_error(EC_STACK_IS_EMPTY);
		return;
	}
	--stack_len;
	memmove(b1.stack, b1.stack+1, sizeof(b1.stack)-sizeof(*b1.stack));
	if (stack_len<MAX_STACK_ELEMENTS) {
		b1.stack[MAX_STACK_ELEMENTS-1].type = VT_EMPTY;
		b1.stack[stack_len].type = VT_EMPTY;
	}
}

bool ok_for_arithmetic()
{
	if (!there_are_no_spurious_args())
		return false;
	if (stack_len<2) {
		print_error(EC_TOO_FEW_OPERANDS);
		return false;
	}
	if (b1.stack[0].type != VT_NUMBER) {
		print_error(EC_TOP_MUST_BE_INT);
		return false;
	}
	if (b1.stack[1].type != VT_NUMBER) {
		print_error(EC_2ND_MUST_BE_INT);
		return false;
	}
	operand1 = b1.stack[0].int_value;
	operand2 = b1.stack[1].int_value;
	cmd_drop();
	return true;
}

static void cmd_mul()
{
	if (ok_for_arithmetic())
		b1.stack[0].int_value = operand1 * operand2;
}

static void cmd_vars()
{
	if (!there_are_no_spurious_args())
		return;
#ifndef DEBUG_SET_VAR
	if ( (dm.mode_flags & debug_mode) != debug_mode ) {
		print_error(EC_ONLY_IN_DEBUG);
		return;
	}
#endif
	printf(CYN "Bank 1:\n" reset);
	bool printed_something = false;
	for(int i=0; i<N_VARS_PER_STORE; ++i) {
#ifdef DEBUG_SET_VAR
		printf("%02d %x %" PRIu64 " ", i, b1.store1_values[i].signer, store1_timestamps[i]);
#endif
		if (*b0.store1_var_names[i]) {
			if (b1.store1_values[i].type == VT_STRING)
				printf(reset "%.32s = " YEL "%.32s\n" reset, b0.store1_var_names[i], b1.store1_values[i].str_id_value);
			else
				printf(reset "%.32s = " YEL "%" PRId64 "\n" reset, b0.store1_var_names[i], b1.store1_values[i].int_value);
			printed_something = true;
		}
	}
	if (!printed_something)
		printf("(empty)\n");
	printed_something = false;
	printf("\n" CYN "Bank 2:\n" reset);
	for(int i=0; i<N_VARS_PER_STORE; ++i) {
#ifdef DEBUG_SET_VAR
		printf("%02d %x %" PRIu64 " ", i, b1.store2_values[i].signer, store2_timestamps[i]);
#endif
		if (*b0.store2_var_names[i]) {
			if (b1.store2_values[i].type == VT_STRING)
				printf(reset "%.32s = " YEL "%.32s\n" reset, b0.store2_var_names[i], b1.store2_values[i].str_id_value);
			else
				printf(reset "%.32s = " YEL "%" PRId64 "\n" reset, b0.store2_var_names[i], b1.store2_values[i].int_value);
			printed_something = true;
		}
	}
	if (!printed_something)
		printf("(empty)\n");
	printf(reset);
}

/* static void cmd_get_int() */
/* { */
/* 	if (!there_are_no_spurious_args()) */
/* 		return; */
/* 	printf("GET_INT ... TODO\n"); */
/* } */

/* static void cmd_set_int() */
/* { */
/* 	if (!there_are_no_spurious_args()) */
/* 		return; */
/* 	printf("SET_INT ... TODO\n"); */
/* } */

static void cmd_get_var()
{
	if (!there_are_no_spurious_args())
		return;
	if (stack_len < 1) {
		print_error(EC_TOO_FEW_OPERANDS);
		return;
	}
	if (b1.stack[0].type != VT_IDENTIFIER) {
		print_error(EC_TOP_MUST_BE_ID);
		return;
	}
	if (lseek(fd_store, 0, SEEK_SET) == -1) {
		perror("cmd_set_str lseek (1)");
		exit(EXIT_FAILURE);
	}
	if (flock(fd_store, LOCK_EX)) {
		perror("cmd_get_var flock LOCK_EX");
		exit(EXIT_FAILURE);
	}
	ssize_t n = read(fd_store, b0.store1_var_names, sizeof(b0.store1_var_names));
	if (n) {
		if (n!=sizeof(b0.store1_var_names)
			|| read(fd_store, store1_timestamps,    sizeof(store1_timestamps))    != sizeof(store1_timestamps)
			|| read(fd_store, b1.store1_values, sizeof(b1.store1_values)) != sizeof(b1.store1_values)
			|| read(fd_store, b0.store2_var_names,  sizeof(b0.store2_var_names))  != sizeof(b0.store2_var_names)
			|| read(fd_store, store2_timestamps,    sizeof(store2_timestamps))    != sizeof(store2_timestamps)
			|| read(fd_store, b1.store2_values, sizeof(b1.store2_values)) != sizeof(b1.store2_values)) {
			perror("cmd_get_var read");
			exit(EXIT_FAILURE);
		}
	}
	if (flock(fd_store, LOCK_UN)) {
		perror("cmd_get_var flock LOCK_UN");
		exit(EXIT_FAILURE);
	}
	for(int i=0; i<N_VARS_PER_STORE; ++i) {
		if (strncmp(b0.store1_var_names[i], b1.stack[0].str_id_value, MAX_STR_ID_LEN)==0) {
			b1.stack[0] = b1.store1_values[i];
			return;
		}
		if (strncmp(b0.store2_var_names[i], b1.stack[0].str_id_value, MAX_STR_ID_LEN)==0) {
			b1.stack[0] = b1.store2_values[i];
			return;
		}
	}
	print_error(EC_UNDEF_VAR);
}

int store_for_identifier(char *identifier)
{
	char id_with_terminator[MAX_STR_ID_LEN + 1];
	memset(id_with_terminator, 0, sizeof(id_with_terminator));
	strncpy(id_with_terminator, identifier, MAX_STR_ID_LEN);
	const size_t len = strlen(id_with_terminator);
	if (*id_with_terminator=='f') {
		if (id_with_terminator[len-1]=='1') return 0;
		if (id_with_terminator[len-1]=='2') return 1;
	}
	uint8_t hash[64]; /* Output hash (64 bytes)          */
	crypto_blake2b(hash, (uint8_t *)id_with_terminator, strlen(id_with_terminator));
	/* for(int a=0;a<64;++a) */
	/* 	printf("%02x", hash[a]); */
	/* printf("\n"); */
	int rv = hash[0] & 1;
#ifdef DEV_DEBUG
	printf("store_for_identifier(%s)=%d\n", id_with_terminator, rv);
#endif
	return rv;
}

static void ints_to_something(int something)
{
	if (!there_are_no_spurious_args())
		return;
	if (stack_len < 4) {
		print_error(EC_TOO_FEW_OPERANDS);
		return;
	}
	for(int a=0; a<4; ++a)
		if (b1.stack[a].type != VT_NUMBER) {
			print_error(EC_TOP_MUST_BE_INTS);
			return;
		}
	uint64_t ints[4];
	for(int a=0; a<4; ++a)
		ints[a] = b1.stack[a].int_value;
	char *p = (char *)ints;
	for(int a=0; a<32; ++a, ++p) {
		if (!*p) {
			if (a==0 && something==VT_IDENTIFIER)
				goto error;
			for(; a<32; ++a)
				*p++ = 0;
			break;
		}
		const char c = *p;
		if ((!isprint(c) && c!='\t' && c!='\r' && c!='\n') || (something==VT_IDENTIFIER && isblank(*p))) {
error:
			print_error(EC_INVALID_OPERAND);
			return;
		}
	}
	cmd_drop();
	cmd_drop();
	cmd_drop();
	b1.stack[0].type = something;
	uint64_t *s = (uint64_t *)b1.stack[0].str_id_value;
	for(int a=0; a<4; ++a)
		s[a] = ints[a];
}

static void cmd_ints_to_str()
{
	ints_to_something(VT_STRING);
}

static void cmd_int_to_str()
{
	if (!there_are_no_spurious_args())
		return;
	if (stack_len < 1) {
		print_error(EC_TOO_FEW_OPERANDS);
		return;
	}
	if (b1.stack[0].type != VT_NUMBER) {
		print_error(EC_TOP_MUST_BE_INT);
		return;
	}
	b1.stack[0].type = VT_STRING;
	const uint64_t i = b1.stack[0].int_value;
	sprintf(b1.stack[0].str_id_value, "%" PRId64, i);
}

static void cmd_ints_to_id()
{
	ints_to_something(VT_IDENTIFIER);
}

static void cmd_str_to_int()
{
	if (!there_are_no_spurious_args())
		return;
	if (stack_len < 1) {
		print_error(EC_TOO_FEW_OPERANDS);
		return;
	}
	if (b1.stack[0].type != VT_STRING) {
		print_error(EC_TOP_MUST_BE_STR);
		return;
	}
	char *p = b1.stack[0].str_id_value;
	if (!*p) goto invalid;
	b1.stack[0].type = VT_NUMBER;
	uint64_t result = strtoll(b1.stack[0].str_id_value, &p, 0);
	if (*p) {
invalid:
		b1.stack[0].type = VT_IDENTIFIER;
		strcpy(b1.stack[0].str_id_value, "Invalid_integer");
		return;
	}
	b1.stack[0].int_value = result;
}

static void str_or_id_to_ints(int from_type)
{
	if (!there_are_no_spurious_args())
		return;
	if (stack_len < 1) {
		print_error(EC_TOO_FEW_OPERANDS);
		return;
	}
	if (b1.stack[0].type != from_type) {
		print_error(EC_TOP_MUST_BE_STR);
		return;
	}
	stack_len += 4;
	if (stack_len > MAX_STACK_ELEMENTS) {
		print_error(EC_STACK_IS_FULL);
		stack_len -= 4;
		return;
	}
	uint64_t ints[4], *p = (uint64_t*)b1.stack[0].str_id_value;
	for(int a=0; a<4; ++a)
		ints[a] = p[a];
	memmove(b1.stack+4, b1.stack, sizeof(b1.stack)-4*sizeof(*b1.stack));
	for(int a=0; a<4; ++a) {
		b1.stack[a].type = VT_NUMBER;
		b1.stack[a].int_value = ints[a];
	}
}

static void cmd_str_to_ints()
{
	str_or_id_to_ints(VT_STRING);
}

static void cmd_id_to_ints()
{
	str_or_id_to_ints(VT_IDENTIFIER);
}

static void cmd_time_to_str()
{
	if (!there_are_no_spurious_args())
		return;
	if (stack_len < 1) {
		print_error(EC_TOO_FEW_OPERANDS);
		return;
	}
	if (b1.stack[0].type != VT_NUMBER) {
		print_error(EC_TOP_MUST_BE_INT);
		return;
	}
	time_t *t = ((time_t *)b1.store2_values) - 1;
	*t = b1.stack[0].int_value;
	if (ctime_r(t, b1.buffer_for_time2str.str_id_value)==b1.buffer_for_time2str.str_id_value) {
		size_t len = strlen(b1.buffer_for_time2str.str_id_value);
		if (len>0 && b1.buffer_for_time2str.str_id_value[len-1]=='\n')
			b1.buffer_for_time2str.str_id_value[--len] = 0;
		b1.stack[0] = b1.buffer_for_time2str;
		b1.stack[0].type = VT_STRING; // the other tag is empty and so should remain
		return;
	}
	print_error_1(EC_TIME_OUT_OF_RANGE, (char*)t);
}

static const uint8_t vk_0[32] = {109, 87, 244, 119, 113, 181, 108, 240, 43, 173, 91, 187, 209, 79, 78, 187, 45, 12, 210, 126, 70, 52, 54, 9, 244, 45, 143, 62, 68, 222, 195, 119};
static const uint8_t vk_1[32] = {9, 113, 217, 78, 218, 199, 4, 235, 186, 44, 80, 3, 59, 133, 19, 68, 86, 195, 159, 143, 2, 115, 21, 250, 60, 186, 250, 169, 79, 201, 192, 164};
static const uint8_t vk_2[32] = {37, 164, 133, 26, 108, 164, 192, 75, 213, 62, 8, 123, 212, 204, 58, 18, 235, 121, 73, 146, 91, 178, 219, 60, 92, 71, 231, 174, 140, 179, 163, 33};
static const uint8_t vk_3[32] = {140, 177, 32, 171, 169, 97, 142, 116, 52, 164, 158, 33, 232, 199, 17, 91, 97, 116, 239, 134, 83, 10, 37, 76, 71, 102, 232, 149, 65, 39, 53, 154};
static const uint8_t vk_4[32] = {204, 241, 52, 95, 137, 29, 223, 176, 117, 238, 95, 143, 247, 17, 149, 130, 132, 127, 87, 138, 238, 68, 190, 89, 99, 111, 7, 99, 227, 29, 124, 77};
static const uint8_t vk_5[32] = {233, 216, 236, 65, 191, 70, 89, 96, 46, 139, 169, 44, 80, 105, 14, 124, 92, 108, 158, 137, 27, 109, 155, 26, 188, 146, 147, 179, 171, 75, 164, 54};
static const uint8_t vk_6[32] = {254, 46, 252, 35, 59, 209, 71, 135, 166, 124, 59, 229, 187, 237, 188, 17, 87, 68, 150, 57, 173, 43, 75, 184, 204, 229, 235, 118, 170, 46, 217, 7};
static const uint8_t vk_7[32] = {244, 207, 47, 6, 60, 74, 166, 225, 90, 156, 97, 228, 91, 253, 136, 98, 228, 45, 200, 13, 141, 38, 82, 70, 102, 229, 67, 79, 103, 100, 39, 242};
static const uint8_t * const v_keys[]={
	vk_0,
	vk_1,
	vk_2,
	vk_3,
	vk_4,
	vk_5,
	vk_6,
	vk_7,
	0,
};

static bool challenge_with_signature()
{
	uint8_t chall[16];
	ssize_t s = getrandom(chall, sizeof(chall), GRND_NONBLOCK);
	if (s != sizeof(chall)) {
		perror("getrandom");
		exit(EXIT_FAILURE);
	}
	printf("In order to store a permanent variable, you must tell me the signature for:\n");
	for(int a=0; a<sizeof(chall); ++a)
		printf("%02x ", chall[a]);
	putchar('\n');
	uint8_t signature[64];
	char line[MAX_LINE_LENGTH];
	if (!fgets(line, sizeof(line), stdin)) {
		printf("Got EOF, bye bye.\n");
		exit(EXIT_FAILURE);
	}
	size_t l = strlen(line);
	if (l && line[l-1]=='\n')
		line[--l] = 0;
	if (l!=128) {
error:
		printf(RED "Nope, sorry.\n" reset);
		return false;
	}
	for(int a=0; a<64; ++a) {
		char s[3];
		s[0] = line[a*2];
		s[1] = line[a*2+1];
		s[2] = 0;
		char *p = 0;
		signature[a] = strtol(s, &p, 16);
		if (*p) goto error;
	}
	for(int i=0; v_keys[i]; ++i) {
		if (crypto_check(signature, v_keys[i], chall, sizeof(chall))==0) {
			/* printf("Signed with key=%d\n", i); */
			++i;
			unsigned char *p = (unsigned char *)&signer;
			for(int a=0; a<4; ++a)
				*p++ = i;
			/* printf("signer=%x\n", signer); */
			return true;
		}
	}
	goto error;
}

static int count_signer(value_t *values, unsigned signer)
{
	unsigned char *p = (unsigned char *)&signer;
	if (signer==-1 || p[0]!=p[1] || p[1]!=p[2] || p[2]!=p[3]) {
		print_error(EC_BAD_SIGNER_TAG);
		exit(EXIT_FAILURE);
	}
	int c = 0;
	for(int a=0; a<N_VARS_PER_STORE; ++a) {
		if (values[a].signer==signer)
			++c;
/* #ifdef DEBUG_SET_VAR */
/* 		printf("values[%d].signer=%x c=%d\n", a, values[a].signer, c); */
/* #endif */
	}
	return c;
}

static void really_set_var(uint64_t *timestamps, char var_names[][MAX_STR_ID_LEN], value_t *values, int store)
{
#ifdef DEBUG_SET_VAR
	printf("Store is %d, signer is %x [entering really_set_var]\n", store, signer);
	for(int i=0; i<N_VARS_PER_STORE; ++i) {
		if (values[i].type == VT_STRING)
			printf("%02d %x %.32s <str> %.32s\n", i, values[i].signer, var_names[i], values[i].str_id_value);
		else if (values[i].type == VT_NUMBER)
			printf("%02d %x %.32s <int> %" PRId64 "\n", i, values[i].signer, var_names[i], values[i].int_value);
		else if (values[i].type) printf("Bad value-type: %u\n", values[i].type);
	}
#endif
	int index = -1;
	for(int a=0; a<N_VARS_PER_STORE; ++a) {
		if (strncmp(var_names[a], b1.stack[0].str_id_value, MAX_STR_ID_LEN)==0) {
			index = a; // the variable already exists, we'll re-use the slot
#ifdef DEBUG_SET_VAR
			printf("Reusing index %d for %.32s\n", index, var_names[a]);
#endif
			if (values[a].signer != signer) {
#ifdef DEBUG_SET_VAR
				printf("Emptying index %d because of different signer\n", a);
#endif
				values[a].type = VT_EMPTY;
				values[a].signer = -1;
				var_names[a][0] = 'A'; /* no variable can legally starts with an uppercase letter */
				index = -1;
			}
			break;
		}
	}
	if (index == -1) {
		const int count = count_signer(values, signer);
#ifdef DEBUG_SET_VAR
		printf("Count = %d\n", count);
#endif
		if (count < MAX_VAR_IN_STORE_PER_SIGNER) { // this signer hasn't used all their slots, there must be unassigned slots
			for(int a=0; a<N_VARS_PER_STORE; ++a)
				if (values[a].signer==-1) {
					index = a;
#ifdef DEBUG_SET_VAR
					printf("Grabbing new-slot = %d\n", index);
#endif
					break;
				}
		} else { // we must re-use the oldest slot
			uint64_t min_timestamp = UINT64_MAX;
			for(int a=0; a<N_VARS_PER_STORE; ++a) {
				if (values[a].signer!=signer)
					continue;
				if (timestamps[a] < min_timestamp) {
					min_timestamp = timestamps[a];
					index = a;
				}
			}
		}
#ifdef DEBUG_SET_VAR
		printf("Using index = %d signer=%x\n", index, values[index].signer);
#endif
		if (index==-1) {
			print_error(EC_CORRUPTED_STORE);
			exit(EXIT_FAILURE);
		}
		memset(var_names[index], 0, MAX_STR_ID_LEN);
		strncpy(var_names[index], b1.stack[0].str_id_value, MAX_STR_ID_LEN);
	}
	timestamps[index] = get_time();
	values[index] = b1.stack[1];
	values[index].signer = signer;
#ifdef DEBUG_SET_VAR
	printf("Store is %d, signer is %x [exiting really_set_var]\n", store, signer);
	for(int i=0; i<N_VARS_PER_STORE; ++i) {
		if (values[i].type == VT_STRING)
			printf("%02d %x %.32s = %.32s\n", i, values[i].signer, var_names[i], values[i].str_id_value);
		else if (values[i].type == VT_NUMBER)
			printf("%02d %x %.32s = %" PRId64 "\n", i, values[i].signer, var_names[i], values[i].int_value);
		else if (values[i].type) printf("Bad value-type: %u\n", values[i].type);
	}
	int c = count_signer(values, signer);
	if (c > MAX_VAR_IN_STORE_PER_SIGNER) {
		printf("\n\n\n**** CORRUPTION for %x, c=%d ****\n\n\n", signer, c);
		exit(-1);
	}
#endif
}

static void cmd_set_var()
{
	if (!there_are_no_spurious_args())
		return;
	if (stack_len < 2) {
		print_error(EC_TOO_FEW_OPERANDS);
		return;
	}
	if (b1.stack[0].type != VT_IDENTIFIER) {
		print_error(EC_TOP_MUST_BE_ID);
		return;
	}
	if (b1.stack[1].type != VT_STRING && b1.stack[1].type != VT_NUMBER) {
		print_error(EC_2ND_MUST_BE_STR_OR_INT);
		return;
	}
	if (!challenge_with_signature()) {
		cmd_drop();
		cmd_drop();
		return;
	}
	if (lseek(fd_store, 0, SEEK_SET) == -1) {
		perror("cmd_set_var lseek (1)");
		exit(EXIT_FAILURE);
	}
	if (flock(fd_store, LOCK_EX)) {
		perror("cmd_set_var flock LOCK_EX");
		exit(EXIT_FAILURE);
	}
	ssize_t n = read(fd_store, b0.store1_var_names, sizeof(b0.store1_var_names));
	if (n) {
		if (n!=sizeof(b0.store1_var_names)
			|| read(fd_store, store1_timestamps, sizeof(store1_timestamps)) != sizeof(store1_timestamps)
			|| read(fd_store, b1.store1_values, sizeof(b1.store1_values)) != sizeof(b1.store1_values)
			|| read(fd_store, b0.store2_var_names,  sizeof(b0.store2_var_names))  != sizeof(b0.store2_var_names)
			|| read(fd_store, store2_timestamps,    sizeof(store2_timestamps))    != sizeof(store2_timestamps)
			|| read(fd_store, b1.store2_values, sizeof(b1.store2_values)) != sizeof(b1.store2_values)) {
			perror("cmd_set_var read");
			exit(EXIT_FAILURE);
		}
	}
	if (store_for_identifier(b1.stack[0].str_id_value)==0) {
		really_set_var(store1_timestamps, b0.store1_var_names, b1.store1_values, 1);
	} else {
		really_set_var(store2_timestamps, b0.store2_var_names, b1.store2_values, 2);
	}
	if (lseek(fd_store, 0, SEEK_SET) == -1) {
		perror("cmd_set_var lseek (2)");
		exit(EXIT_FAILURE);
	}
	if (write(fd_store, b0.store1_var_names, sizeof(b0.store1_var_names)) != sizeof(b0.store1_var_names)) {
		perror("cmd_set_var write (1)");
		exit(EXIT_FAILURE);
	}
	if (write(fd_store, store1_timestamps, sizeof(store1_timestamps)) != sizeof(store1_timestamps)) {
		perror("cmd_set_var write (2)");
		exit(EXIT_FAILURE);
	}
	if (write(fd_store, b1.store1_values, sizeof(b1.store1_values)) != sizeof(b1.store1_values)) {
		perror("cmd_set_var write (3)");
		exit(EXIT_FAILURE);
	}
	if (write(fd_store, b0.store2_var_names, sizeof(b0.store2_var_names)) != sizeof(b0.store2_var_names)) {
		perror("cmd_set_var write (4)");
		exit(EXIT_FAILURE);
	}
	if (write(fd_store, store2_timestamps, sizeof(store2_timestamps)) != sizeof(store2_timestamps)) {
		perror("cmd_set_var write (5)");
		exit(EXIT_FAILURE);
	}
	if (write(fd_store, b1.store2_values, sizeof(b1.store2_values)) != sizeof(b1.store2_values)) {
		perror("cmd_set_var write (6)");
		exit(EXIT_FAILURE);
	}
	if (flock(fd_store, LOCK_UN)) {
		perror("cmd_set_var flock LOCK_UN");
		exit(EXIT_FAILURE);
	}
	if (fsync(fd_store)) {
		perror("cmd_set_var fsync");
		exit(EXIT_FAILURE);
	}
	cmd_drop();
	cmd_drop();
}

static void cmd_pick()
{
	if (n_tokens < 1) {
		print_error(EC_MISSING_ARGUMENT);
		return;
	}
	if (tokens[1].type != TOK_NUMBER) {
		print_error(EC_ARGUMENT_MUST_BE_INT);
		return;
	}
	int i = tokens[1].int_value;
	if (i==0) {
		print_error(EC_OPERAND_MUST_BE_NON_NEG);
		return;
	}
	const unsigned int t = b1.stack[i-1].type;
	if (i>stack_len || t == VT_EMPTY || (t!=VT_NUMBER && t!=VT_STRING && t!=VT_IDENTIFIER)) {
		print_error(EC_THERE_IS_NOTHING);
		return;
	}
	memmove(b1.stack+1, b1.stack, sizeof(b1.stack)-sizeof(*b1.stack));
	++stack_len;
	b1.stack[0] = b1.stack[i];
}

static void cmd_xor()
{
	if (ok_for_arithmetic())
		b1.stack[0].int_value = operand1 ^ operand2;
}

static void cmd_or()
{
	if (ok_for_arithmetic())
		b1.stack[0].int_value = operand1 | operand2;
}

static void cmd_debug_on()
{
	if (!there_are_no_spurious_args())
		return;
	if (!dev_mode)
		print_error(EC_DEBUG_ONLY_IN_DEV);
	else
		dm.mode_flags |= debug_mode;
}

static void cmd_debug_off()
{
	if (!there_are_no_spurious_args())
		return;
	if (!dev_mode)
		print_error(EC_DEBUG_ONLY_IN_DEV);
	else
		dm.mode_flags &= ~debug_mode;
}

typedef struct cmd_tree_node {
	int64_t hash;
	cmd_func_t func;
	struct cmd_tree_node *l, *r;
} cmd_tree_node;

static bool auto_print_stack = true;

static void cmd_ps_on()
{
	auto_print_stack = true;
}

static void cmd_ps_off()
{
	auto_print_stack = false;
}

static void cmd_ps_status()
{
	if ((stack_len+1) > MAX_STACK_ELEMENTS) {
		print_error(EC_STACK_IS_FULL);
		return;
	}
	++stack_len;
	memmove(b1.stack+1, b1.stack, sizeof(b1.stack)-sizeof(*b1.stack));
	b1.stack[0].type = VT_NUMBER;
	b1.stack[0].int_value = auto_print_stack;
}

static void cmd_eval()
{
	extern cmd_tree_node *cmd_tree_root;
	if (!there_are_no_spurious_args())
		return;
	if (stack_len < 1) {
		print_error(EC_TOO_FEW_OPERANDS);
		return;
	}
	if (b1.stack[0].type != VT_NUMBER) {
		print_error(EC_TOP_MUST_BE_INT);
		return;
	}
	uint64_t i = b1.stack[0].int_value;
	cmd_drop();
	cmd_tree_node *p = cmd_tree_root;
	for(int a=0; a<21; ++a) {
		int direction = i&7;
		i >>= 3;
		if (direction == 2) {
			/* printf("l"); */
			p = p->l;
			if (!p) {
error:
				print_error(EC_INVALID_KEYWORD);
				return;
			}
		} else if (direction == 5) {
			/* printf("r"); */
			p = p->r;
			if (!p) goto error;
		} else if (direction==0 || direction==7) {
			goto error;
		} else {
			/* printf("a"); */
		}
	}
	/* printf(""); */
	p->func();
}

#include "cmd_tree.h"

static cmd_func_t find_cmd_func(char *lexeme, int64_t *h)
{
	*h = 0;
	for(char *s=lexeme;*s;++s) {
		const char c = *s;
		if (!((c>='a' && c<='z') || (c>='A' && c<='_'))) {
			print_error_1(EC_INVALID_CHAR_IN_KW, tokens[n_tokens].lexeme);
			return 0;
		}
		*h <<= 5;
		int x = *s & 31;
		*h |= x;
	}
	cmd_tree_node *p = cmd_tree_root;
	while (p) {
		if (p->hash == *h) return p->func;
		p = *h < p->hash ? p->l : p->r;
	}
	print_error_1(EC_INVALID_KEYWORD, lexeme);
	return 0;
}

static void welcome()
{
	printf( BYEL
"                                         .__                  .__             __                   \n"
"_______ ______    ____     ____  _____   |  |    ____   __ __ |  |  _____   _/  |_   ____  _______ \n"
"\\_  __ \\\\____ \\  /    \\  _/ ___\\ \\__  \\  |  |  _/ ___\\ |  |  \\|  |  \\__  \\  \\   __\\ /  _ \\ \\_  __ \\\n"
" |  | \\/|  |_> >|   |  \\ \\  \\___  / __ \\_|  |__\\  \\___ |  |  /|  |__ / __ \\_ |  |  (  <_> ) |  | \\/\n"
" |__|   |   __/ |___|  /  \\___  >(____  /|____/ \\___  >|____/ |____/(____  / |__|   \\____/  |__|   \n"
"        |__|         \\/       \\/      \\/            \\/                   \\/                        \n"

/* BCYN "R" WHT "everse-" BCYN "P" WHT "rogrammer " BCYN "N" WHT "otation " BCYN "Calculator" */
reset "\n\n");
}

#ifndef NO_SECCOMP
static void install_seccomp() {
  static unsigned char filter[] = {32,0,0,0,0,0,0,0,53,0,12,0,0,0,0,64,21,0,12,0,0,0,0,0,21,0,11,0,1,0,0,0,21,0,10,0,3,0,0,0,21,0,9,0,60,0,0,0,21,0,8,0,231,0,0,0,21,0,7,0,228,0,0,0,21,0,6,0,73,0,0,0,21,0,5,0,8,0,0,0,21,0,4,0,74,0,0,0,21,0,3,0,201,0,0,0,21,0,2,0,62,1,0,0,6,0,0,0,1,0,5,0,6,0,0,0,0,0,0,0,6,0,0,0,0,0,255,127};
  struct prog {
    unsigned short len;
    unsigned char *filter;
  } rule = {
    .len = sizeof(filter) >> 3,
    .filter = filter
  };
  if(prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) { perror("prctl(PR_SET_NO_NEW_PRIVS)"); exit(2); }
  if(prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &rule) < 0) { perror("prctl(PR_SET_SECCOMP)"); exit(2); }
}
#endif

static bool is_comment(char *l)
{
	return *l=='#' || (*l=='/' && l[1]=='/');
}

static bool is_ok_for_starting_identifier(char c)
{
	return c=='_' || (c>='a' && c<='z');
}

static bool is_ok_for_identifier(char c)
{
	return c=='_' || isalnum(c);
}

static bool convert_hex_to_long(int64_t *result)
{
	char *p = b0.int_literal_conversion_buffer;
	for(int a=0; a<sizeof(b0.int_literal_conversion_buffer)-1; ++a) {
		*p = tokens[n_tokens].lexeme[a];
		const char c = *p++;
		if (!c) break;
		if (!( c=='-' || c=='+' || c=='x' || c=='X' || (c>='0' && c<='9') || (c>='a' && c<='f') || (c>='A' && c<='Z'))) {
			print_error_1(EC_INVALID_CHAR_IN_INT_LITERAL, b0.int_literal_conversion_buffer);
			return false;
		}
	}
	*result = strtoll(b0.int_literal_conversion_buffer, &p, 16);
	if (*p) {
		print_error_1(EC_INVALID_INT_LITERAL, tokens[n_tokens].lexeme);
		return false;
	}
	return true;
}

static bool convert_oct_to_long(int64_t *result)
{
	char *p = b0.int_literal_conversion_buffer;
	for(int a=0; a<sizeof(b0.int_literal_conversion_buffer); ++a) {
		*p = tokens[n_tokens].lexeme[a];
		const char c = *p++;
		if (!c) break;
		if (!( c=='-' || c=='+' || (c>='0' && c<='7') )) {
			print_error_1(EC_INVALID_CHAR_IN_INT_LITERAL, b0.int_literal_conversion_buffer);
			return false;
		}
	}
	*result = strtoll(b0.int_literal_conversion_buffer, &p, 8);
	if (*p) {
		print_error_1(EC_INVALID_INT_LITERAL, tokens[n_tokens].lexeme);
		return false;
	}
	return true;
}

static bool my_convert_to_long(int64_t *result)
{
	const char * const s = tokens[n_tokens].lexeme;
	if (strlen(s) > sizeof(b0.int_literal_conversion_buffer)) {
		print_error_1(EC_INT_LITERAL_TOO_LONG, tokens[n_tokens].lexeme);
		return false;
	}
	memset(b0.int_literal_conversion_buffer, 0, sizeof(b0.int_literal_conversion_buffer));
	if (s[0] == '0') {
		if (s[1]=='x' || s[1]=='X')
			return convert_hex_to_long(result);
		else
			return convert_oct_to_long(result);
	}
	if ((s[0] == '+' || s[0]=='-') && s[1]=='0') {
		if (s[2]=='x' || s[2]=='X')
			return convert_hex_to_long(result);
		else
			return convert_oct_to_long(result);
	}
	char *p = b0.int_literal_conversion_buffer;
	for(int a=0; a<sizeof(b0.int_literal_conversion_buffer)-1; ++a) {
		*p = tokens[n_tokens].lexeme[a];
		const char c = *p++;
		if (!c) break;
		if (!( (a==0 && (c=='-' || c=='+')) || (c>='0' && c<='9'))) {
			print_error_1(EC_INVALID_CHAR_IN_INT_LITERAL, b0.int_literal_conversion_buffer);
			return false;
		}
	}
	*result = strtoll(b0.int_literal_conversion_buffer, &p, 10);
	if (*p) {
		print_error_1(EC_INVALID_INT_LITERAL, tokens[n_tokens].lexeme);
		return false;
	}
	return true;
}

struct shortcut {
	char op;
	char *lexeme;
} shortcuts[] = {
	{ '+', "Add" },
	{ '-', "Sub" },
	{ '*', "Mul" },
	{ '/', "Div" },
	{ '&', "And" },
	{ '^', "Xor" },
	{ '|', "Or" },
	{ '?', "Help" },
	{ 0, 0 }
};

bool check_shortcuts(char *l) {
	for(struct shortcut *s = shortcuts; s->op; ++s)
		if (l[0]==s->op && (l[1]==0 || isblank(l[1]))) {
			tokens[n_tokens].type = TOK_KEYWORD;
			tokens[n_tokens].lexeme = s->lexeme;
			cmd_func_t f = find_cmd_func(tokens[n_tokens].lexeme, &tokens[n_tokens].int_value);
			if (!f) {
				print_error(EC_INTERNAL_PARSER_ERROR);
				exit(EXIT_FAILURE);
			}
			tokens[n_tokens].kw_function = f;
			n_tokens++;
			return true;
		}
	return false;
}

static char *input_continuation = 0;
static bool auto_eval = 0;

static bool tokenize(char *l)
{
	for(int a=0; a<MAX_TOKENS; ++a)
		tokens[a].type = TOK_NONE;
	n_tokens = 0;
	auto_eval = 0;
	for(;;) {
		if (!*l) return true;
		if (isblank(*l)) {
			++l;
			continue;
		}
		if (*l == ';') {
			input_continuation = l+1;
			return true;
		}
		if (is_comment(l))
			return true;
		if (check_shortcuts(l)) {
			++l;
			continue;
		}
		if (is_ok_for_starting_identifier(*l)) {
			tokens[n_tokens].type = TOK_IDENT;
			tokens[n_tokens].lexeme = l;
			char *end = ++l;
			while (is_ok_for_identifier(*end)) ++end;
			if ( (end-tokens[n_tokens].lexeme) > MAX_STR_ID_LEN ) {
				print_error_1(EC_IDENT_TOO_LONG, tokens[n_tokens].lexeme);
				return 0;
			}
			++n_tokens;
			if (!*end)
				return true;
			*end = 0;
			l = ++end;
			continue;
		} else if ((*l>='0' && *l<='9') || ((*l=='-' || *l=='+') && l[1]>='0' && l[1]<='9')) {
			tokens[n_tokens].type = TOK_NUMBER;
			tokens[n_tokens].lexeme = l;
			char *end = ++l;
			while (*end && !isblank(*end)) ++end;
			if (end[-1]=='!') {
				auto_eval = true;
				end[-1] = 0;
			}
			l = *end ? end+1 : end;
			*end = 0;
			if (!my_convert_to_long(&tokens[n_tokens].int_value))
				return false;
			++n_tokens;
			continue;
		} if (*l=='\"' || *l=='\'') {
			l = parse_string_literal(l);
			if (!l)
				return false;
		} else if (*l >= 'A' && *l <= '_') {
			tokens[n_tokens].type = TOK_KEYWORD;
			tokens[n_tokens].lexeme = l;
			char *end = ++l;
			while (*end && !isblank(*end)) {
				++end;
			}
			l = *end ? end+1 : end;
			*end = 0;
			const cmd_func_t f = strcasecmp(tokens[n_tokens].lexeme, "peek")==0 ? cmd_peek : find_cmd_func(tokens[n_tokens].lexeme, &tokens[n_tokens].int_value);
			if (!f)
				return false;
			tokens[n_tokens].kw_function = f;
			n_tokens++;
			continue;
		} else {
			print_error_1(EC_UNEXPECTED_INPUT, l);
			return false;
		}
	}
}

static void clear_store(value_t *values)
{
	for(int a=0; a<N_VARS_PER_STORE; ++a) {
		values[a].type = VT_EMPTY;
		values[a].signer = a < MAX_VAR_IN_STORE_PER_SIGNER ? 0x01010101 : -1;
	}
}

static int open_store(char *filename)
{
	clear_store(b1.store1_values);
	clear_store(b1.store2_values);
	b1.pad0.type = VT_STRING;
	for(int a=0; a<MAX_STACK_ELEMENTS; ++a)
		b1.stack[a].signer = -1;
	int fd = open(filename, O_CREAT|O_RDWR, 0600);
	if (fd<0) {
		perror("open");
		exit(EXIT_FAILURE);
	}
	return fd;
}

void load_var_stores()
{
	if (lseek(fd_store, 0, SEEK_SET) == -1) {
		perror("load_var_stores lseek");
		exit(EXIT_FAILURE);
	}
	if (flock(fd_store, LOCK_EX)) {
		perror("load_var_stores flock LOCK_EX");
		exit(EXIT_FAILURE);
	}
	ssize_t n = read(fd_store, b0.store1_var_names, sizeof(b0.store1_var_names));
	if (n) {
		if (n!=sizeof(b0.store1_var_names)
			|| read(fd_store, store1_timestamps, sizeof(store1_timestamps)) != sizeof(store1_timestamps)
			|| read(fd_store, b1.store1_values, sizeof(b1.store1_values)) != sizeof(b1.store1_values)
			|| read(fd_store, b0.store2_var_names,  sizeof(b0.store2_var_names))  != sizeof(b0.store2_var_names)
			|| read(fd_store, store2_timestamps,    sizeof(store2_timestamps))    != sizeof(store2_timestamps)
			|| read(fd_store, b1.store2_values, sizeof(b1.store2_values)) != sizeof(b1.store2_values)) {
			perror("load_var_stores read");
			exit(EXIT_FAILURE);
		}
	}
	if (flock(fd_store, LOCK_UN)) {
		perror("load_var_stores flock LOCK_UN");
		exit(EXIT_FAILURE);
	}
}

void init_random()
{
	static int counter = -1;
	if (counter++ == 0) {
		/* printf("random()=%ld\n", random()); */
		srandom(time(0));
		/* printf("random()=%ld\n", random()); */
	}
}

int main()
{
	setvbuf(stdout, NULL, _IONBF, 0);
	setvbuf(stderr, NULL, _IONBF, 0);
	setvbuf(stdin, NULL, _IONBF, 0);
	fd_store = open_store(FLAG_STORE_FILENAME);
#ifndef NO_SECCOMP
	install_seccomp();
#endif
	load_var_stores();
	welcome();
	cmd_help();
	dev_mode = getenv("DEVELOPMENT_MODE")!=0;
	char line[MAX_LINE_LENGTH];
	for(;;) {
		if (input_continuation) {
			char *c = input_continuation;
			input_continuation = 0;
			if (!tokenize(c) || n_tokens==0)
				continue;
		} else {
			init_random();
			putchar('\n');
			if (auto_print_stack)
				print_stack();
			printf(CYN "Ready");
#ifdef DEV_DEBUG
			if ((dm.mode_flags & debug_mode) == debug_mode)
				printf(" (debug-mode enabled)");
#endif
			printf(".\n" reset "> ");
			if (!fgets(line, sizeof(line), stdin)) {
				printf("Got EOF, bye bye.\n");
				break;
			}
			const size_t l = strlen(line);
			if (l && line[l-1]=='\n')
				line[l-1] = 0;
			if (!tokenize(line) || n_tokens==0)
				continue;
		}
		/* print_tokens(); */
		enum tok_type tt = tokens[0].type;
		if (tt == TOK_KEYWORD) {
			if (tokens[0].kw_function)
				tokens[0].kw_function();
		} else {
			if (n_tokens > 1) {
				print_error(EC_TOO_MANY_TOKENS);
				continue;
			}
			switch(tt) {
			case TOK_IDENT:
				push_ident(tokens);
				break;
			case TOK_NUMBER:
				push_int(tokens);
				if (auto_eval) {
					auto_eval = false;
					cmd_eval();
				}
				break;
			case TOK_STRING:
				push_string(tokens);
				break;
			default:
				assert(0);
			}
		}
	}
}

