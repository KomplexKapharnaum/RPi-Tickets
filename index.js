var express = require('express');
var app = express();
var server = require('http').createServer(app);
var io = require('socket.io')(server);
var fs = require('fs')
var path = require('path')
var in_array = require('in_array')
var sharp = require('sharp');

var LISTPATH = '/media/usb'
//var LISTPATH = '/home/mgr/Pictures'
var EXTENSION = ['.jpg', '.jpeg', '.png', '.bmp']

var PeerMachine = require('./kpi-peers/peermachine.js')();
PeerMachine.on( 'logguer.log', (data, from)=>console.log('received', data, ' <- ',from) );
PeerMachine.on('doPrint', (data)=>print(data))
PeerMachine.start();


var printer = require("node-thermal-printer");
printer.init({
  type: 'epson',
  // interface: '/dev/bus/usb/001/007'
  interface: '/dev/usb/lp0'
});

printer.isPrinterConnected( function(isConnected){
  console.log('Printer state', isConnected)
  /*printer.println("Hello world");
  printer.cut();
  printer.execute(); */
})

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
    else if (in_array(path.extname(file).toLowerCase(), EXTENSION)) fileList.push(entry)

  })
  fileList.sort(compare)
  return fileList
}

function print(job) {
  var filepath = LISTPATH+job['relpath']
  console.log("Resize and Print image", filepath)
  if (job['nbr'] < 1) return;
  sharp(filepath)
    .resize(576)
    .png()
    .toBuffer()
    .then( data => {
      //printer.alignCenter()
      printer.printImageBuffer(data, function(done){
        if (job['cut']) printer.cut()
        printer.execute((err) => {
          if (err) console.error("Print failed", err);
          else {
            console.log("Print done");
            job['nbr'] -= 1
            setTimeout(()=>print(job), job['pause'])
          }
        });
      })
    })
    .catch( err => console.log('Resize failed') );
}

app.use(express.static(__dirname + '/www/'));
app.get('/', function(req, res,next) {
    res.sendFile(__dirname + '/www/index.html');
});

io.on('connection', function(client) {
    console.log('Client connected...');

    client.on('getlist', function(data) {
      var list = allFilesSync(LISTPATH)
      client.emit('listNode', list)
    });

    client.on('print', function(data) {
      //print(data)
      PeerMachine.broadcast('doPrint', data)
    });

});

function countingPeers() {
  // console.log(PeerMachine.peersCount())
  io.emit('peers', PeerMachine.peersCount())
}
setInterval(countingPeers, 3000);

server.listen(4200);
