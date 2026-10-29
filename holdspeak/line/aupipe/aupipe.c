/*
 * aupipe: a baresip audio source and player over two unix sockets.
 *
 * Copyright (c) 2026, HoldSpeak contributors. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of HoldSpeak nor the names of its contributors may be
 *    used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 * HoldSpeak's Line (docs/internal/betterment/line/LINE-DESIGN-2026-10-29.md
 * section 6). It uses only baresip's and libre's public module API
 * (both BSD-3-Clause); it links no other library.
 *
 *   audio_source  aupipe,/path/say.sock    (we read s16le PCM the Line sends)
 *   audio_player  aupipe,/path/heard.sock  (we write the caller's s16le PCM)
 *
 * The module is the client: it connects to the socket the Line serves, and
 * tries again each frame while it is not connected. With no PCM to send, the
 * source sends silence. A full socket drops the caller's frame (never blocks).
 */
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <re_atomic.h>
#include <re.h>
#include <rem.h>
#include <baresip.h>

struct pipe_conn {
	char path[256];
	int fd;
};

static void conn_close(struct pipe_conn *c)
{
	if (c->fd >= 0)
		close(c->fd);
	c->fd = -1;
}

static bool conn_ensure(struct pipe_conn *c)
{
	struct sockaddr_un sa;
	int fd;

	if (c->fd >= 0)
		return true;
	fd = socket(AF_UNIX, SOCK_STREAM, 0);
	if (fd < 0)
		return false;
	memset(&sa, 0, sizeof(sa));
	sa.sun_family = AF_UNIX;
	str_ncpy(sa.sun_path, c->path, sizeof(sa.sun_path));
	if (connect(fd, (struct sockaddr *)&sa, sizeof(sa)) < 0) {
		close(fd);
		return false;
	}
	fcntl(fd, F_SETFL, fcntl(fd, F_GETFL) | O_NONBLOCK);
#ifdef SO_NOSIGPIPE
	{ int one = 1; setsockopt(fd, SOL_SOCKET, SO_NOSIGPIPE, &one, sizeof(one)); }
#endif
	c->fd = fd;
	info("aupipe: connected %s\n", c->path);
	return true;
}

/* ---- the source: PCM in from the Line, out into the call ---- */

struct ausrc_st {
	struct pipe_conn conn;
	struct ausrc_prm prm;
	thrd_t thread;
	RE_ATOMIC bool run;
	ausrc_read_h *rh;
	void *arg;
	int16_t *sampv;
	size_t sampc;
	size_t have;     /* bytes of the next frame already read */
};

static void src_destructor(void *arg)
{
	struct ausrc_st *st = arg;
	if (re_atomic_rlx(&st->run)) {
		re_atomic_rlx_set(&st->run, false);
		thrd_join(st->thread, NULL);
	}
	conn_close(&st->conn);
	mem_deref(st->sampv);
}

static int src_thread(void *arg)
{
	struct ausrc_st *st = arg;
	uint64_t t = tmr_jiffies();
	size_t bytes = st->sampc * sizeof(int16_t);

	while (re_atomic_rlx(&st->run)) {
		struct auframe af;
		int dt;

		if (conn_ensure(&st->conn)) {
			ssize_t n = read(st->conn.fd,
					 (uint8_t *)st->sampv + st->have,
					 bytes - st->have);
			if (n > 0)
				st->have += (size_t)n;
			else if (n == 0 || (errno != EAGAIN && errno != EWOULDBLOCK))
				conn_close(&st->conn);
		}

		if (st->have == bytes) {
			auframe_init(&af, AUFMT_S16LE, st->sampv, st->sampc,
				     st->prm.srate, st->prm.ch);
			af.timestamp = t * 1000;
			st->rh(&af, st->arg);
			st->have = 0;
		}
		else {
			/* not a whole frame yet: silence, keep the partial */
			int16_t *sil = mem_zalloc(bytes, NULL);
			if (sil) {
				auframe_init(&af, AUFMT_S16LE, sil, st->sampc,
					     st->prm.srate, st->prm.ch);
				af.timestamp = t * 1000;
				st->rh(&af, st->arg);
				mem_deref(sil);
			}
		}

		t += st->prm.ptime;
		dt = (int)(t - tmr_jiffies());
		if (dt > 0)
			sys_msleep(dt);
	}
	return 0;
}

static int src_alloc(struct ausrc_st **stp, const struct ausrc *as,
		     struct ausrc_prm *prm, const char *dev,
		     ausrc_read_h *rh, ausrc_error_h *errh, void *arg)
{
	struct ausrc_st *st;
	int err;
	(void)as; (void)errh;

	if (!stp || !prm || !rh || !str_isset(dev))
		return EINVAL;
	if (prm->fmt != AUFMT_S16LE)
		return ENOTSUP;

	st = mem_zalloc(sizeof(*st), src_destructor);
	if (!st)
		return ENOMEM;
	st->conn.fd = -1;
	str_ncpy(st->conn.path, dev, sizeof(st->conn.path));
	st->prm = *prm;
	if (!st->prm.ptime)
		st->prm.ptime = 20;
	st->rh = rh;
	st->arg = arg;
	st->sampc = prm->srate * prm->ch * st->prm.ptime / 1000;
	st->sampv = mem_zalloc(st->sampc * sizeof(int16_t), NULL);
	if (!st->sampv) {
		err = ENOMEM;
		goto out;
	}
	info("aupipe: source %s %u Hz %u ch ptime %u\n", dev, prm->srate,
	     prm->ch, st->prm.ptime);
	re_atomic_rlx_set(&st->run, true);
	err = thread_create_name(&st->thread, "aupipe_src", src_thread, st);
	if (err)
		re_atomic_rlx_set(&st->run, false);
 out:
	if (err)
		mem_deref(st);
	else
		*stp = st;
	return err;
}

/* ---- the player: the caller's PCM out of the call, to the Line ---- */

struct auplay_st {
	struct pipe_conn conn;
	struct auplay_prm prm;
	thrd_t thread;
	RE_ATOMIC bool run;
	auplay_write_h *wh;
	void *arg;
	int16_t *sampv;
	size_t sampc;
};

static void play_destructor(void *arg)
{
	struct auplay_st *st = arg;
	if (re_atomic_rlx(&st->run)) {
		re_atomic_rlx_set(&st->run, false);
		thrd_join(st->thread, NULL);
	}
	conn_close(&st->conn);
	mem_deref(st->sampv);
}

static int play_thread(void *arg)
{
	struct auplay_st *st = arg;
	uint64_t t = tmr_jiffies();
	size_t bytes = st->sampc * sizeof(int16_t);

	while (re_atomic_rlx(&st->run)) {
		struct auframe af;
		int dt;

		auframe_init(&af, AUFMT_S16LE, st->sampv, st->sampc,
			     st->prm.srate, st->prm.ch);
		af.timestamp = t * 1000;
		st->wh(&af, st->arg);

		if (conn_ensure(&st->conn)) {
#ifdef MSG_NOSIGNAL
			ssize_t n = send(st->conn.fd, st->sampv, bytes, MSG_NOSIGNAL);
#else
			ssize_t n = send(st->conn.fd, st->sampv, bytes, 0);
#endif
			if (n < 0 && errno != EAGAIN && errno != EWOULDBLOCK)
				conn_close(&st->conn);
		}

		t += st->prm.ptime;
		dt = (int)(t - tmr_jiffies());
		if (dt > 0)
			sys_msleep(dt);
	}
	return 0;
}

static int play_alloc(struct auplay_st **stp, const struct auplay *ap,
		      struct auplay_prm *prm, const char *dev,
		      auplay_write_h *wh, void *arg)
{
	struct auplay_st *st;
	int err;
	(void)ap;

	if (!stp || !prm || !wh || !str_isset(dev))
		return EINVAL;
	if (prm->fmt != AUFMT_S16LE)
		return ENOTSUP;

	st = mem_zalloc(sizeof(*st), play_destructor);
	if (!st)
		return ENOMEM;
	st->conn.fd = -1;
	str_ncpy(st->conn.path, dev, sizeof(st->conn.path));
	st->prm = *prm;
	st->wh = wh;
	st->arg = arg;
	st->sampc = prm->srate * prm->ch * prm->ptime / 1000;
	st->sampv = mem_zalloc(st->sampc * sizeof(int16_t), NULL);
	if (!st->sampv) {
		err = ENOMEM;
		goto out;
	}
	info("aupipe: player %s %u Hz %u ch ptime %u\n", dev, prm->srate,
	     prm->ch, prm->ptime);
	re_atomic_rlx_set(&st->run, true);
	err = thread_create_name(&st->thread, "aupipe_play", play_thread, st);
	if (err)
		re_atomic_rlx_set(&st->run, false);
 out:
	if (err)
		mem_deref(st);
	else
		*stp = st;
	return err;
}

static struct ausrc *ausrc;
static struct auplay *auplay;

static int module_init(void)
{
	int err;
	err  = ausrc_register(&ausrc, baresip_ausrcl(), "aupipe", src_alloc);
	err |= auplay_register(&auplay, baresip_auplayl(), "aupipe", play_alloc);
	return err;
}

static int module_close(void)
{
	ausrc = mem_deref(ausrc);
	auplay = mem_deref(auplay);
	return 0;
}

EXPORT_SYM const struct mod_export DECL_EXPORTS(aupipe) = {
	"aupipe",
	"sound",
	module_init,
	module_close
};
