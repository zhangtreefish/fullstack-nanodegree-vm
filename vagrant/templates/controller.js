'use strict';

/**
 * @ngdoc object
 * @name therapeuticFoodsApp
 * @requires $routeProvider
 * @requires foodsControllers
 * @requires ui.bootstrap
 *
 * @description
 * Root app, which routes and specifies the partial html and controller depending on the url requested.
 * when(path, route): Adds a new route definition to the $route service.
 */
var app = angular.module('therapeuticFoodsApp',
    ['foodsControllers', 'ngRoute', 'ui.bootstrap']).
    config(['$routeProvider',
        function ($routeProvider) {
            $routeProvider.
                when('/login/', {
                    templateUrl: '/partials/login.html',
                    controller: 'loginCtrl'
                }).
                otherwise({
                    redirectTo: '/'
                });
        }]);


//Change the delimiter notation for Angular to allow expression in a new form of {a some_variable a}
app.config(['$interpolateProvider', function($interpolateProvider) {
  $interpolateProvider.startSymbol('{a');
  $interpolateProvider.endSymbol('a}');
}]);
