define([
  'libs/xdate'
], function(XDate) {
 var app = angular.module('booker', []);
 
 var GROUP_NAMES = [
     { name: "This Week", id: "thisWeek" },
     { name: "Next Week", id: "nextWeek" }
 ]
 
 app.factory('Bookings', function($http) {
   return {
     getBookings: $http.bind(this, {
       method: 'GET',
       url: '/bookings',
       cache: true
     })
   };
 });
 
 app.factory('RangeUtils', function() {
 
   var _makeRange = function(w, y) {
     var start = new XDate;
     start.setWeek(w, y);
 
     var stop = new XDate(start)
     stop.addDays(7);
 
     return [start, stop];
   }
 
   return {
     getRangeForDate: function(d) {
       var today = new XDate;
 
       var currentWeek = today.getWeek();
       if (d == 'nextWeek') {
         currentWeek += 1;
       }
 
       return _makeRange(currentWeek, today.getFullYear()).map(function(d) {
         return d[0];
       });
     }
   };
 });
 
 app.directive('booking', function() {
   return {
     restrict: 'C',
     templateUrl: 'booking.html',
     scope: {
       data: '='
     }
   };
 });
 
 app.directive('groupSelector', function() {
 
   var linkFn = function($scope, $el, $attrs) {
     $scope.changeActiveGroup = function(groupId) {
       $scope.active = groupId;
     }
   }
 
   return {
     restrict: 'C',
     templateUrl: 'group-selector.html',
     link: linkFn,
     scope: {
       groups: '=',
       active: '='
     }
   };
 });
 
 app.filter('filterBooking', function(RangeUtils) {
   return function(els, type) {
     var ranges = RangeUtils.getRangeForDate(type);
     var start = ranges[0];
     var stop = ranges[1];
 
     els = els || [];
     return els.filter(function(e) {
       var d = e.date;
       return (d >= start) && (d <= stop);
     });
 
   }
 });
 
 app.controller('MainController', function($scope, Bookings) {
 
   // Set the group selector and default active group
   $scope.groups = GROUP_NAMES;
   $scope.activeGroup = 'thisWeek';
 
   Bookings.getBookings().then(function(res) {
     $scope.bookings = res.data.map(function(d) {
       return { name: d.name, status: d.status, date: new Date(d.date) };
     }).sort(function(b1, b2) {
       if (b1.date == b2.date) return 0;
       return b1.date > b2.date ? -1 : 1;
     });
   });
 });
 
 app.config(function($interpolateProvider) {
   $interpolateProvider.startSymbol('{[{');
   $interpolateProvider.endSymbol('}]}');
 });

 return app;
});

