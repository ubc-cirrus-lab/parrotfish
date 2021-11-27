# adapted from https://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html#sig-v4-examples-post
import hmac, hashlib, datetime, os

class IAMAuth:
    def __init__(self, host, stage, resource, service='execute-api', content='application/x-amz-json-1.0') -> None:
        self.access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        self.secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.content_type = content
        self.service = service
        self.host = host
        self.region = host.split('.')[2]
        self.stage = stage
        self.resource = resource
        pass

    def _sign(self, key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _getSignatureKey(self, key, date_stamp, regionName, serviceName):
        kDate = self._sign(('AWS4' + key).encode('utf-8'), date_stamp)
        kRegion = self._sign(kDate, regionName)
        kService = self._sign(kRegion, serviceName)
        kSigning = self._sign(kService, 'aws4_request')
        return kSigning

    def getHeader(self, payload, method='POST'):
        t = datetime.datetime.utcnow()
        amz_date = t.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope

        canonical_querystring = ''
        canonical_headers = 'content-type:' + self.content_type + '\n' + 'host:' + self.host + '\n' + 'x-amz-date:' + amz_date + '\n' 
        signed_headers = 'content-type;host;x-amz-date'
        payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        canonical_uri = '/' + self.stage + '/' + self.resource
        canonical_request = method + '\n' +canonical_uri +'\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = date_stamp + '/' + self.region + '/' + self.service + '/' + 'aws4_request'
        string_to_sign = algorithm + '\n' +  amz_date + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        signing_key = self._getSignatureKey(self.secret_key, date_stamp, self.region, self.service)
        signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()
        authorization_header = algorithm + ' ' + 'Credential=' + self.access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
        headers = {'Content-Type':self.content_type,
                   'X-Amz-Date':amz_date,
                   'Authorization':authorization_header}
        return headers