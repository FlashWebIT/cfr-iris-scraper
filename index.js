var exec = require('child_process').exec,
    cheerio = require('cheerio'),
    cheerioTableparser = require('cheerio-tableparser'),
	commandExistsSync = require('command-exists').sync,
	path = require('path'),
    express = require('express')();

// Check if PhantomJS can be ran on the system
if (!commandExistsSync('phantomjs')) {
	process.stderr.write(
		"Could not find PhantomJS on this system. " +
		"Please ensure that PhantomJS is installed and can be ran " +
		"from the current path.\n" +
		"http://phantomjs.org/\n"
	);
    process.exit(1);
}

express.get('/station/:id*', function(req, res, next) {
	cmd = 'phantomjs ' + path.resolve(__dirname, 'station.js') + ' ' + req.params['id'];
	
	exec(cmd, function(error, stdout, stderr) {
		if (error !== null) {
			console.log('Execution error: ' + error);
			
			res.statusCode = 500;
			res.send('Internal error.');
			return;
		}
		
		res.setHeader('Access-Control-Allow-Origin', '*');
		var output = [];
		
		// Get the retrieved HTML table from PhantomJS
		$ = cheerio.load(stdout);
		cheerioTableparser($);
		var data = $("table").parsetable(true, true, true);
		
		if (data.length != 0) {
			var newArray = data[0].map(function(col, i) {
				return data.map(function(row) {
					return row[i];
				});
			});
			newArray.shift();
			
			// Push each entry in the table into the output array
			for (var i = 0; i < newArray.length; i++) {
				// Split the origin and final stations from their respective times
				if (newArray[i][3]) {
					from = newArray[i][3].split(/[0-9]/)[0].replace(/\s\s*$/, '');
					originatingdepart = newArray[i][3].match(/([0-9\:]+)/)[0]; 
				} else { 
					from = ''; originatingdepart = '';
				}
				
				if (newArray[i][7]) {
					to = newArray[i][7].split(/[0-9]/)[0].replace(/\s\s*$/, '');
					finalarrive = newArray[i][7].match(/([0-9\:]+)/)[0]
				} else {
					to = ''; finalarrive = '';
				}
				
				// Push the output
				output.push({
					ID:			newArray[i][1],
					Rank:		newArray[i][0],
					Operator:	newArray[i][2],
					
					Origin: from,
					OriginDeparture: originatingdepart,
					
					Destination: to,
					DestinationArrival: finalarrive,
					
					Arrival: newArray[i][5],
					Departure: newArray[i][6],
					
					Line: newArray[i][8],
					Delay: newArray[i][4]
				});
			} 
		}
		
		// Send the output
		res.send(JSON.stringify(output));
	});
});

express.get('/train/:id*', function(req, res, next) {
	cmd = 'phantomjs  ' + path.resolve(__dirname, 'train.js') + ' ' + req.params['id'];
	
	exec(cmd, function(error, stdout, stderr) {
		if (error !== null) {
			console.log('Execution error: ' + error);
			
			res.statusCode = 500;
			res.send('Internal error.');
			return;
		}
		
		res.setHeader('Access-Control-Allow-Origin', '*');
		var output = [];
		
		// Get the retrieved HTML table from PhantomJS
		$ = cheerio.load(stdout);
		cheerioTableparser($);
		var data = $("table").parsetable(true, true, true);
		
		if (data.length != 0) {
			/*
			 * Remove the last two elements of the data array, 
			 * since the table does contain other UI elements
			 * we don't care about.
			*/
			data.splice(2, 2);
			
			TrainStatus = data[1][4];
			TrainInCirculation = (TrainStatus === "In circulatie");
			TrainArrived = (TrainStatus === "Sosit la destinatie");
			TrainAwaitingDeparture = (TrainStatus === "Asteapta plecarea");

			// Save the output
			var TrainInfo = {
				ID: 						data[1][1],
				Rank:						data[1][0],
				
				Operator:					data[1][2],
				
				Route:						data[1][3],
				Distance:					data[1][12],
				RouteDuration:				data[1][13],
				
				TrainStatus:				TrainStatus,				
				TrainInCirculation:			TrainInCirculation,
				TrainArrived:				TrainArrived,
				TrainAwaitingDeparture:		TrainAwaitingDeparture,
				
				LatestInfo:					data[1][5],
				LatestInfoTime:				data[1][6],
				
				Delay:						data[1][7],
				
				Destination:				data[1][8],
				DestinationArriveTime:		data[1][9],
				
				NextStop:					data[1][10],
				NextStopTime:				data[1][11]
			};
			
			output = {
				Info:	TrainInfo,
			};
		}
		
		// Send the output
		res.send(JSON.stringify(output));
	});
});

process.on('uncaughtException', function (err) {
	console.log('Caught unhandled exception: ' + err);
});

express.listen(9090);