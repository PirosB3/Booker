require.config({
    baseUrl: "/static/js",
    shim: {
      'libs/jquery': {exports: 'jQuery'},
      'libs/xdate': {exports: 'XDate'},
      'libs/angular': {
        exports: 'angular',
        deps: ['libs/jquery']
      }
    }
});

window.name = "NG_DEFER_BOOTSTRAP!";

require(['libs/angular'], function() {
    require(['main'], function(app) {
       angular.element().ready(function() {
           angular.resumeBootstrap([app['name']]);
       });
    });
});


