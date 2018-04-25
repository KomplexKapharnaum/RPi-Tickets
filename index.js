var express = require('express');
var bodyParser = require("body-parser");
var fileUpload = require('express-fileupload');
var app = express();
var server = require('http').createServer(app);
var io = require('socket.io')(server);
var fs = require('fs')
var path = require('path')
var in_array = require('in_array')
const { spawnSync} = require('child_process');

var WEBPORT = 80

var LISTPATH = '/media/usb'
//var LISTPATH = '/home/mgr/Pictures'
var EXTENSION = ['.jpg', '.jpeg', '.png', '.bmp', '.pdf']

var PeerMachine = require('./kpi-peers/peermachine.js')();
PeerMachine.on( 'logguer.log', (data, from)=>console.log('received', data, ' <- ',from) );
PeerMachine.on('doPrint', (job)=>print(job))
PeerMachine.start();


printPy(path.resolve(__dirname, 'blank.png'), 1, true, 0)

function print(job) {
  fs.writeFileSync('/tmp/'+job.relpath, job.data);
  printPy('/tmp/'+job.relpath, job.nbr, job.cut, job.pause)
}

function printPy(filepath, nbr, cut, pause) {
  nbr -= 1
  if (nbr < 0) {
    if(fs.existsSync(filepath)) fs.unlink(filepath)
    return;
  }
  const child = spawnSync(path.resolve(__dirname, 'py-print/print'), [filepath, (cut)?1:0]);
  // console.log(child.stdout.toString());
  setTimeout(()=>printPy(filepath, nbr, cut, pause), pause)
}


app.use(express.static(__dirname + '/www/'));
//app.use(bodyParser.urlencoded({ extended: false }));
//app.use(bodyParser.json());
app.use(fileUpload());
app.get('/', function(req, res,next) {
    res.sendFile(__dirname + '/www/index.html');
});
app.post('/printFile', function(req, res) {
    // console.log(req.files.upload)

    if (req.files.upload) {
      if (!Array.isArray(req.files.upload)) req.files.upload = [req.files.upload]
      for (let file of req.files.upload) {
        // console.log(file)

        var job = {data: file.data, nbr: 1, cut:1, pause: 0, relpath: file.name}
        PeerMachine.broadcast('doPrint', job)

        // fs.writeFileSync('/tmp/'+file.name, file.data);
        // printPy('/tmp/'+file.name, 1, 1, 1);
        // fs.unlink('/tmp/'+file.name)
      }
    }

    // The name of the input field (i.e. "sampleFile") is used to retrieve the uploaded file
    // let sampleFile = req.files.sampleFile;
    res.sendFile(__dirname + '/www/index.html');
});

io.on('connection', function(client) {
    console.log('Client connected...');

    client.on('getlist', function(data) {
      var list = allFilesSync(LISTPATH)
      client.emit('listNode', list)
    });

    client.on('printUsb', function(job) {
      //print(data)
      var filepath = LISTPATH+job['relpath']
      job['data'] = fs.readFileSync(filepath)
      PeerMachine.broadcast('doPrint', job)
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
