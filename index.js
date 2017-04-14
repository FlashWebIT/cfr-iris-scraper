var exec = require('child_process').exec,
    cheerio = require('cheerio'),
    cheerioTableparser = require('cheerio-tableparser'),
    data = [], output = [], newArray;
    express = require('express')();

express.get('/station/:id*', function(req, res, next) {
  cmd = 'phantomjs station.js '+req.params['id'];

  exec(cmd, function(error, stdout, stderr) {
    $ = cheerio.load(stdout);
    cheerioTableparser($);
    data = $("table").parsetable(true, true, true);
    if (data.length != 0) { newArray = data[0].map(function(col, i) { 
        return data.map(function(row) { 
          return row[i] 
        })
      });
    newArray.shift();
    output = [];
    for (var i = 0; i < newArray.length; i++) {
    	if (newArray[i][3]) { from = newArray[i][3].split(/[0-9]/)[0].replace(/\s\s*$/, ''); originatingdepart = newArray[i][3].match(/([0-9\:]+)/)[0]; } else { from = ''; originatingdepart = ''; }
    	if (newArray[i][7]) { to = newArray[i][7].split(/[0-9]/)[0].replace(/\s\s*$/, ''); finalarrive = newArray[i][7].match(/([0-9\:]+)/)[0] } else  { to = ''; finalarrive = ''; }
      output.push({train: newArray[i][1], type: newArray[i][0], operator: newArray[i][2], from: from, originatingdepart: originatingdepart, to: to, finalarrive: finalarrive, arrive: newArray[i][5], depart: newArray[i][6], line: newArray[i][8], delay: newArray[i][4]});
    } }
  res.send(JSON.stringify(output));
});  

});

express.listen(9090);