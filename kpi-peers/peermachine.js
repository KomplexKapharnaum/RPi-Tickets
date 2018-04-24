var portastic = require('portastic');
var IoServer = require('./ioserver.js')

function PeerMachine()
{
    var that = this;
    this.server = null;
    this.modules = [];
    this.callbacks = {};

    /**
    SERVERS
    **/

    this.start = function(portastic_options) {
        if (portastic_options === undefined) portastic_options = { min : 9000, max : 32000 }
        // Find free port
        portastic.find(portastic_options).then(function(ports) {
            var port = ports[0];
            //port = ports[Math.floor(Math.random()*ports.length)];

            that.server = new IoServer(port, 'KPi-peer');

            // create Main Channel
            var machine = that.server.addChannel('/peer').p2p();

            // create Event Channel
            var events_channel = that.server.addChannel('/event/peer');

            // Route Machine input to modules
            machine.on('/input', that.execute);

            // Route Machine state events to event channel
            machine.on('/state', events_channel.send);

            // inform new RADIO client of Machine status (known peers and methods)
            events_channel.on('/state/newclient', function(ev, cli) {

                var status = { peers: {}, methods: that.getMethods() };
                var peers = machine.activeLinks();
                for (var name in peers) status.peers[name] = peers[name].url;
                //console.log(status);
                events_channel.send('/status', status, Object.keys(cli)[0]);
            });

            // machine.on('/output', function(cmd, data) {
            //     //console.log('OUTPUT: ', cmd, data);
            // })

            // Declare Bonjour
            that.server.advertize();

            // Give event channel to all attached modules
            for (var m of that.modules)
                if (!m._events) m._events = that.server.addChannel('/event'+m._procid);
        });
    }

    //attach path to callback
    this.on = function(path, clbk) {
      path = path.replace('.', '/')
      if (path[0] != '/') path = '/'+path;
      if (!this.callbacks[path]) this.callbacks[path] = []
      this.callbacks[path].push(clbk)
    }

    // attach new module
    this.attach = function(id, object) {
        id = id.replace('.', '/')
        if (id[0] != '/') id = '/'+id;
        object._procid = id;
        this.modules.push(object);

        // create event channel
        if (that.server)
            object._events = that.server.addChannel('/event'+id);
    }

    // transmit command to modules
    this.execute = function(path, message) {

        // Route to attached modules
        var cmd = path.split('/');  // cmd[1] is the processor id, cmd[2] is the method call
        if (!cmd[2]) cmd[2] = 'default'; // default method if none provided
        for (var proc of that.modules)
            if (proc._procid == '/'+cmd[1]) proc.do(cmd[2], message.data);
        //console.log('CMD: '+path+' '+JSON.stringify(message.data));

        // Route to bound callbacks
        if (that.callbacks[path])
          for (var clbk of that.callbacks[path]) clbk(message.data, message.from)
    }

    // list available methods in modules
    this.getMethods = function() {
        var methods = {};
        for (var proc of this.modules)
            methods[ proc._procid ] = proc.description();
        return methods;
    }

    // Get name
    this.name = function() {
        if(that.server) return this.server.name;
    }

    // TOOLS
    this.command = function(cmd, data, to) {
        if(that.server) that.server.channel('/peer').send(cmd, data, to);
    }

    this.broadcast = function(cmd, data) {
      if(that.server) that.server.channel('/peer').send(cmd, data);
    }

    this.publish = function(news, data) {
        if(that.server) that.server.channel('/info').send(news, data);
    }

}

var exports = module.exports = function() { return new PeerMachine() };
