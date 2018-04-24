var os = require('os');
var bonjour = require('bonjour')();
var socketio_server = require('socket.io');
var socketio_client = require('socket.io-client');
var socketio_wildcard = require('socketio-wildcard');

const STATE_DROPPED = 0;
const STATE_CONNECTING = 1;
const STATE_ACCEPTED = 2;

function P2P(channel) {

    channel.masters = {};        // own Clients connected to remote servers

    // Check if connected to (rewrite to include Masters)
    channel.isConnectedTo = function(name) {
        if (channel.slaves[name]) return (channel.slaves[name].status > STATE_DROPPED);
        else if (channel.masters[name]) return (channel.masters[name].status > STATE_DROPPED);
        return false;
    }

    // List of clients (rewrite to include Masters)
    channel.getClients = function(status, type) {
        var peers = {};

        var m = [];
        for (var name in channel.masters)
            if (!status || status == channel.masters[name].status)
                if (!type || type == channel.masters[name].type) {
                    peers[name] = channel.masters[name];
                    m.push(name);
                }

        var s = [];
        for (var name in channel.slaves)
            if (!status || status == channel.slaves[name].status)
                if (!type || type == channel.slaves[name].type) {
                    peers[name] = channel.slaves[name];
                    s.push(name);
                }

        // console.log(' ');
        // console.log('IAM: '+channel.device.name);
        // console.log('MASTER of: '+JSON.stringify(s));
        // console.log('SLAVE to: '+JSON.stringify(m));
        // console.log('--');

        return peers;
    }

    channel.activeLinks = function() {
        return channel.getClients(STATE_ACCEPTED, channel.device.type);
    }

    // Search for other MASTERS
    bonjour.find({ type: channel.device.type }, function (service)
    {
        // Check if a connection already exist
        if (channel.isConnectedTo(service.name)) return;
        else if (service.name == channel.device.name) return;

        // Connect to master
        var master = {
                io: socketio_client(service.host+channel.channel),
                statut: STATE_CONNECTING,
                name: service.name,
                url: service.host,
                type: channel.device.type,
                drop: function() { this.status = STATE_DROPPED; this.io.disconnect(); },
                accept: function() { this.status = STATE_ACCEPTED; channel.listen(this); },
                send: function(cmd, msg) { channel.send(cmd, msg, this.name); }
            }
        socketio_wildcard(socketio_client.Manager)(master.io);

        master.io.on('connect', function(){ master.io.emit('iam',
            {name: channel.device.name, url: channel.device.url, type: channel.device.type}); });

        master.io.on('drop',    function() { master.drop() });
        master.io.on('accept',  function(){
            if (channel.isConnectedTo(service.name)) master.drop();
            else master.accept();
        });
        channel.masters[service.name] = master;
        channel.emitEvent('/state/newserver', {[master.name]: master.url});
    });

    return channel;
}


function Channel(mainserver, namespace) {
    var that = this;

    this.device = mainserver;
    this.channel = namespace;
    this.slaves = {};         // remote Clients connected to my server
    this.callbacks = {};

    // Create MASTER Server
    this.server = this.device.io.of(namespace);
    this.server.use(socketio_wildcard());
    this.server.on('connection', function (client)
    {
        // New Slave trying to connect
        client.on('iam', function(cli) {
            var slave = {
                    io: client,
                    name: cli.name,
                    url: cli.url,
                    type: cli.type,
                    status: STATE_CONNECTING,
                    drop: function() { this.status = STATE_DROPPED; this.io.emit('drop'); },
                    accept: function() { this.status = STATE_ACCEPTED; this.io.emit('accept'); that.listen(this); },
                    send: function(cmd, msg) { that.send(cmd, msg, this.name); }
                };

            if (that.isConnectedTo(cli.name)) slave.drop();
            else slave.accept();

            // register that slave
            that.slaves[cli.name] = slave;

            that.emitEvent('/state/newclient', {[slave.name]: slave.url});
        });

        // Slave is gone
        client.on('disconnect', function(){
            var s = that.find(client);
            if (s) delete that.slaves[ s.name ];
        });
    });

    this.find = function(client) {
        for (var name in that.slaves)
            if (client.id == that.slaves[name].io.id) return that.slaves[name];
    }

    this.isConnectedTo = function(name) {
        if (this.slaves[name]) return (this.slaves[name].status > STATE_DROPPED);
        return false;
    }

    this.listen = function(client) {
        client.io.on('*', function(input){
            if (client.status == STATE_DROPPED) return;
            var path = input.data[0];
            if (path[0] != '/') return;
            var message = input.data[1];
            if (message === undefined) message = { data: null};
            that.emitEvent('/input'+path, message);
        });
    }

    this.on = function(event, fn) {
        if (!this.callbacks[event]) this.callbacks[event] = [];
        this.callbacks[event].push(fn);
    }

    this.emitEvent = function(event, data) {
        for (var ev in this.callbacks)
            if (event.indexOf(ev) === 0) {
                var msg = '/';
                if (ev.length < event.length) msg = event.substring(ev.length);
                for (var fn of this.callbacks[ev]) //console.log(fn.toString(), msg, data.data);
                    fn(msg, data);
            }
    }

    // List all clients with status
    this.getClients = function(status, type) {
        var peers = {};

        for (var name in this.slaves)
            if (!status || status == this.slaves[name].status)
                if (!type || type == this.slaves[name].type)
                    peers[name] = this.slaves[name];

        return peers;
    }

    this.activeLinks = function() {
        return this.getClients(STATE_ACCEPTED, this.device.type);
    }

    this.send = function(cmd, payload, to) {
        cmd = cmd.replace('.', '/')
        if (cmd[0] != '/') cmd = '/'+cmd;
        if (cmd[0] != '/') console.error('Invalid command: '+cmd);

        var message = {
            from: that.device.name,
            channel: that.channel,
            data: payload,
            to: to
        };

        var peers = that.getClients(STATE_ACCEPTED);

        // Send to all
        if (!to) {
            for (var name in peers) peers[name].io.emit(cmd, message);
            that.emitEvent('/input'+cmd, message);
        }

        // Send to device
        else if (peers[to]) peers[to].io.emit(cmd, message);
        else if (to == that.name) that.emitEvent('/input'+cmd, message);

        //console.log('SEND: ', cmd, message, Object.keys(that.getClients()));
        that.emitEvent('/output'+cmd, message);
    }

    this.p2p = function() {
        return P2P(this);
    }

    return that;
}

function Server(port, type)
{
    var that = this;
    this.type = type;
    this.url = 'http://'+getIPAddress()+':'+port;
    this.name = os.hostname()+':'+port;
    this.port = port;
    this.channels = {};

    // open socket.io server
    this.io = socketio_server(port);


    this.addChannel = function(ch) {
        if (this.channels[ch]) return this.channels[ch];
        this.channels[ch] = new Channel(this, ch);
        return this.channels[ch];
    }

    this.channel = function(ch) {
        return this.channels[ch];
    }

    this.advertize = function() {
        // Advertize Device
        bonjour.publish({ name: this.name, host: this.url, type: this.type, port: this.port });
        console.log ('PEERMACHINE: "'+this.name+'" started on '+this.url);
    }
}

function getIPAddress() {
  var interfaces = os.networkInterfaces();
  for (var devName in interfaces) {
    var iface = interfaces[devName];
    for (var i = 0; i < iface.length; i++) {
      var alias = iface[i];
      if (alias.family === 'IPv4' && alias.address !== '127.0.0.1' && !alias.internal)
        return alias.address;
    }
  }
  return os.hostname();
}

var exports = module.exports = Server;
