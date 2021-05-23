from spruned.application.context import ctx as _ctx, Context
from spruned.daemon.zeromq import build_zmq


def builder(ctx: Context):  # pragma: no cover
    from spruned.application.cache import CacheAgent
    from spruned.repositories.repository import Repository
    from spruned.daemon.tasks.blocks_reactor import BlocksReactor
    from spruned.daemon.tasks.headers_reactor import HeadersReactor
    from spruned.application import vo_service
    from spruned.application.jsonrpc_server import JSONRPCServer
    from spruned.daemon.electrum import build as electrum_builder
    from spruned.daemon.p2p import build as p2p_builder

    electrum_connectionpool, electrum_interface = electrum_builder(ctx)
    p2p_connectionpool, p2p_interface = p2p_builder(ctx)
    repository = Repository.instance()
    cache = CacheAgent(repository, int(ctx.cache_size))
    repository.set_cache(cache)
    service = vo_service.VOService(
        electrum_interface,
        p2p_interface,
        repository=repository,
        cache_agent=cache,
        context=ctx
    )
    jsonrpc_server = JSONRPCServer(ctx.rpcbind, ctx.rpcport, ctx.rpcuser, ctx.rpcpassword)
    jsonrpc_server.set_vo_service(service)
    headers_reactor = HeadersReactor(repository.blockchain, p2p_interface)

    if ctx.mempool_size:
        from spruned.application.mempool_observer import MempoolObserver
        mempool_observer = MempoolObserver(repository, p2p_interface)
        headers_reactor.add_on_new_header_callback(mempool_observer.on_block_header)
        p2p_interface.mempool = repository.mempool
        p2p_connectionpool.add_on_transaction_callback(mempool_observer.on_transaction)
        p2p_connectionpool.add_on_transaction_hash_callback(mempool_observer.on_transaction_hash)
    else:
        mempool_observer = None
    zmq_context = zmq_observer = None
    if ctx.is_zmq_enabled():
        zmq_context, zmq_observer = build_zmq(
            ctx,
            mempool_observer,
            headers_reactor,
            ctx.mempool_size,
            service
        )
    blocks_reactor = BlocksReactor(repository, p2p_interface, keep_blocks=int(ctx.keep_blocks))
    return jsonrpc_server, headers_reactor, blocks_reactor, repository, \
           cache, zmq_context, zmq_observer, p2p_interface


jsonrpc_server, headers_reactor, blocks_reactor, repository, \
    cache, zmq_context, zmq_observer, p2p_interface = builder(_ctx)
