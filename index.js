var express = require('express');
var bodyParser = require("body-parser");
var fileUpload = require('express-fileupload');
var app = express();
var server = require('http').createServer(app);
var io = require('socket.io')(server);
var fs = require('fs')
var path = require('path')
var in_array = require('in_array')
const { spawnSync, exec} = require('child_process');

var WEBPORT = 80

var LISTPATH = '/media/usb'
//var LISTPATH = '/home/mgr/Pictures'
var EXTENSION = ['.jpg', '.jpeg', '.png', '.bmp', '.pdf']

var PeerMachine = require('./kpi-peers/peermachine.js')();
PeerMachine.on( 'logguer.log', (data, from)=>console.log('received', data, ' <- ',from) );
PeerMachine.on('doPrint', (job)=>{
  // console.log('JOB received via KPi-ppers: ', job)
  for (var k=0; k<job.nbr; k++)
    for (var file of job.files) {
      worker.enqueue( new Task(file.relpath, job.cut, file.data, job.pause) )
    }

})
PeerMachine.start();

class Task {
  constructor(path, cut, data, wait) {
    this.path = JSON.parse(JSON.stringify(path))
    this.cut = cut
    this.data = data
    this.wait = wait
  }
  execute(work) {
    // console.log('/'+this.path)
    print(this.path, this.cut, this.data, ()=>{
      setTimeout(()=>{work.next()}, this.wait)
    })
  }
}

class Worker {
  constructor() {
    var that = this
    this.tasks = []
    this.running = false
  }
  next() {
    if (this.tasks.length > 0) this.tasks.pop().execute(this)
    else this.running = false
  }
  enqueue(newtask) {
    this.tasks.unshift(newtask)
    if (!this.running) {
      this.running = true
      this.next()
    }
  }
}

var worker = new Worker()

print('blank.png', 1, fs.readFileSync(path.resolve(__dirname, 'blank.png')))

function print(relpath, cut, buffer, onEnd) {
  console.log('-'+relpath)
  var filepath
  if (buffer) {
    filepath = '/tmp/'+relpath
    fs.writeFileSync(filepath, buffer);
  }
  else filepath = LISTPATH+relpath

  var cmd = path.resolve(__dirname, 'py-print/print')+" "+filepath+" "+((cut=='1')?"1":"0")
  console.log(cmd)
  exec(cmd, (err, stdout, stderr) => {
    if(fs.existsSync(filepath) && filepath.startsWith('/tmp')) fs.unlink(filepath)
    if (err) {
      console.error(`exec error: ${err}`);
      return;
    }
    if (onEnd) onEnd()
  });
}



app.use(express.static(__dirname + '/www/'));
app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());
app.use(fileUpload());
app.get('/', function(req, res,next) {
    res.sendFile(__dirname + '/www/index.html');
});
app.post('/printFile', function(req, res) {
     console.log(req.body)
    var job = {
      files: [],
      cut: req.body.cut,
      nbr: req.body.nbr,
      pause: req.body.pause,
    }

    for (var p of req.body.relpath.split(',')) {
      job.files.push({relpath:p, data:null})
      console.log(p)
    }

    if (req.files.upload) {
      if (!Array.isArray(req.files.upload)) req.files.upload = [req.files.upload]
      for (let file of req.files.upload) {
        job.files.push({relpath:file.name, data:file.data})
      }
    }

    PeerMachine.broadcast('doPrint', job)
    // The name of the input field (i.e. "sampleFile") is used to retrieve the uploaded file
    // let sampleFile = req.files.sampleFile;
    res.redirect('/');
    // res.sendFile(__dirname + '/www/index.html');

});

io.on('connection', function(client) {
    console.log('Client connected...');

    client.on('getlist', function(data) {
      var list = allFilesSync(LISTPATH)
      client.emit('listNode', list)
    });

    client.on('printUsb', function(job) {
      //print(data)
      // var filepath = LISTPATH+job['relpath']
      // job['data'] = fs.readFileSync(filepath)
      //PeerMachine.broadcast('doPrint', job)
    });

});

function countingPeers() {
  // console.log(PeerMachine.peersCount())
  io.emit('peers', PeerMachine.peersCount())
}
setInterval(countingPeers, 3000);

// LIST USB FILES
function compare(a,b) {
  var aName = a.name.toLowerCase()
  var bName = b.name.toLowerCase()
  if (a.children !== undefined) aName = 'aa'+aName
  if (b.children !== undefined) bName = 'aa'+bName
  if (aName < bName) return -1;
  if (aName > bName) return 1;
  return 0;
}

const allFilesSync = (dir, fileList = []) => {
  fs.readdirSync(dir).forEach(file => {
    const filePath = path.join(dir, file)
    var entry =  {name: file, path: filePath, relpath: filePath.split(LISTPATH)[1] }
    if (fs.statSync(filePath).isDirectory()) {
      entry['children'] = allFilesSync(filePath)
      if (entry['children'].length > 0) fileList.push(entry)
    }
    else if (in_array(path.extname(file).toLowerCase(), EXTENSION) && file[0] != '.') fileList.push(entry)

  })
  fileList.sort(compare)
  return fileList
}

server.listen(WEBPORT);
