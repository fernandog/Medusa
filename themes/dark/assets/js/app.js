(window.webpackJsonp=window.webpackJsonp||[]).push([[3],{252:function(o,e,n){"use strict";n.r(e);var t=n(9),a=n(33),c=n(25),s=n(22),i=n(6);t.a.config.devtools=!0,t.a.config.performance=!0,Object(a.c)(),Object(a.b)();const d=new t.a({name:"app",router:c.b,store:s.a,data:()=>({globalLoading:!1,pageComponent:!1}),mounted(){if(i.f&&console.log("App Mounted!"),!window.location.pathname.includes("/login")){const{$store:o}=this;Promise.all([o.dispatch("login",{username:window.username}),o.dispatch("getConfig"),o.dispatch("getStats")]).then(([o,e])=>{i.f&&console.log("App Loaded!");const n=new CustomEvent("medusa-config-loaded",{detail:e.main});window.dispatchEvent(n)}).catch(o=>{console.debug(o),alert("Unable to connect to Medusa!")})}}}).$mount("#vue-wrap");e.default=d}},[[252,1,0,2]]]);
//# sourceMappingURL=app.js.map