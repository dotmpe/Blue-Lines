comment(
    """
    The root HTML template and the outer frame of the page.
    """
),
html(lang='en', xmlns=xmlns)#XXX: html Ns:, **{'xmlns:foo':'s:/bar'}) 
[
  head 
  [
    title[ '⎇ Blue Lines' ],

    link( rel="stylesheet", type="text/css",
      href="/media/style/default.css", ),

    #script( type="application/javascript",
    #  src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js"),
    script( type="application/javascript",
      src="/script/lib/jquery-1.4.2.min.js"),
    #script( type="text/javascript",
    #  src="https://www.google.com/jsapi", ),
    #script( type="text/javascript" )[ 
    #  """ google.load("jquery", "1.3.2"); """ ],

    slot('head-script'),
    #script( type='$type', src='$src' ) * scripts
  ],
  body#(_class='autowidth') 
  [
    slot( 'body-0' ),
  ]
]

# vim:et:ts=2:sw=2:ft=python:
