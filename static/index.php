<?php
	// Include all the configuration files
	include("include/noscript.conf.php");
	
	// Libraries initialization
	
	// Twig
	require_once 'lib/Twig/Autoloader.php';
	Twig_Autoloader::register();

	$loader = new Twig_Loader_Filesystem('templates');
	$twig = new Twig_Environment($loader, array(
		//'cache' => '/path/to/compilation_cache',
		'cache' => false,
	));
	
	// Determine what is the required page
	$reqPage = 'index';
	if(isset($_GET['p']) && !empty($_GET['p']))
		$reqPage = $_GET['p'];
	
	// Keep the H@X0RS busy
	$reqPage = preg_replace('/[^A-Za-z0-9_\-]/', '_', $reqPage);
	
	// Run the page's script, if needed
	$outputArr = array();
	
	if(!in_array($reqPage, $noScript, true))
		// TODO: Try-Catch
		if(file_exists("scripts/$reqPage.php"))
			include "scripts/$reqPage.php";
		else
			die("Unde mi-e scriptu' bo$$?");
	
	// Display template
	// TODO: Try-Catch
	if(file_exists("templates/$reqPage.twig"))
		$twig->display("$reqPage.twig", $outputArr);
	else
		die("N-am templeit sa muara mama!");	