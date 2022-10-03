opts = weboptions();
url = "https://www.mmo-scorelocomotives.org";
url1 = url + "/api-token-auth/";
url2 = url + "/api/get_route_list/";
url3 = url + "/api/get_route_data/";
% opts.Username = "demo";
% opts.Password = "locomotives";
opts.RequestMethod = 'post';
% opts.ContentType = 'json';
opts.CertificateFilename = "../arl_custom_cert_bundle.pem";

payload = struct('username', 'demo', 'password', 'locomotives');

response = webwrite(url1, payload, opts);
% disp(response);
opts.HeaderFields = {'Authorization', ['Token ', response.token] };
% disp(opts);
opts.RequestMethod = 'get';
routes = webread(url2, opts);

disp(routes);

% not sure why Matlab prefixes an "x" on the keys
disp(routes.x2);

route = webread(url3+'2/', opts);

disp(route);

disp(route.segments(1));
