package com.db.bankapi.codesample;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.ws.rs.client.ClientBuilder;
import jakarta.ws.rs.client.Entity;
import jakarta.ws.rs.client.WebTarget;
import jakarta.ws.rs.core.Form;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.NewCookie;
import jakarta.ws.rs.core.Response;
import org.apache.commons.codec.binary.Base64;
import org.glassfish.jersey.client.ClientProperties;

import java.io.IOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * If you setup this application in your local environment/IDE, we recommend maven as build tool with the following
 * dependency configurations:
 * <pre>
 *  <dependencies>
 * 		<dependency>
 * 			<groupId>org.glassfish.jersey.core</groupId>
 * 			<artifactId>jersey-client</artifactId>
 * 			<version>3.1.3</version>
 * 		</dependency>
 * 		<dependency>
 * 			<groupId>org.glassfish.jersey.inject</groupId>
 * 			<artifactId>jersey-hk2</artifactId>
 * 			<version>3.1.3<</version>
 * 		</dependency>
 * 		<dependency>
 * 			<groupId>org.glassfish.jersey.media</groupId>
 * 			<artifactId>jersey-media-json-jackson</artifactId>
 * 			<version>3.1.3<</version>
 * 		</dependency>
 * 		<dependency>
 * 			<groupId>jakarta.activation</groupId>
 * 			<artifactId>jakarta.activation-api</artifactId>
 * 			<version>2.1.2</version>
 * 		</dependency>
 * 		<dependency>
 * 			<groupId>commons-codec</groupId>
 * 			<artifactId>commons-codec</artifactId>
 * 			<version>1.16.0</version>
 * 		</dependency>
 * 	</dependencies>
 * </pre>
* Para ejecutar esta aplicación de muestra, debe adaptar 4 parámetros:
*
* Primero, las variables FKN y PIN de una de sus cuentas de usuario de prueba de Deutsche Bank que creó
* en https://developer.db.com/dashboard/testusers
*
* Luego reemplace el parámetro de consulta "Client_ID" en el paso 1, así como en el paso 5 con el cliente de una de sus aplicaciones de simulación que usa
* El código de código de autorización fluye con la clave de prueba para el tipo de subvención de intercambio de código (PKCE).El último parámetro que debe adaptarse es el parámetro de consulta "redirect_uri"
* Con un URIS de redirección correspondiente de su aplicación elegida.Este parámetro también se usa en el Paso 1 y el Paso 5 de esta aplicación de muestra.
*
* ¡Uso del flujo del código de autorización con PKCE, previene los ataques de inyección de CSRF y del código de autorización!
* En este ejemplo no se usa un secreto del cliente.Presupuestos que esta aplicación es un cliente público en lugar de un cliente confidencial.
* Si desarrolla un cliente confidencial, puede usar un secreto de cliente.A los clientes públicos no pueden usar un secreto del cliente porque no pueden mantener en secreto al cliente de manera segura.
* Para obtener más información, lea nuestras diferencias entre un cliente público y confidencial en nuestras preguntas frecuentes en https://developer.db.com/faq.
* La extensión PKCE requiere un paso adicional al principio y una verificación adicional al final:
*
* Primero cree una cadena aleatoria criptográfica de alta entrapía entre 43 y 128 caracteres usando
* Los caracteres no reservados [A-Z] / [A-Z] / [0-9] / "-" / "."/ "_" / "~".Este es su verificador de código.
*
* Desde su verificador de código, debe crear un desafío de código que tenga que ser calificado con SHA-256 y luego enviado como cadena codificada Base64 URL.
* Ambos se envían al servidor de autorización en diferentes pasos del flujo OAuth 2.0 para permitir la autorización
* Servidor para verificar que se comunique solo con su aplicación.
*
* ¡¡Atención!!Use https://simulator-api.db.com/gw/oidc/managegrants/ para eliminar el consentimiento de
* Su identificación de cliente (aplicación) que usa en este ejemplo si se da antes.De lo contrario, obtendrá un NullPointerException después de otorgar
* ¡Acceso a los ámbitos porque ya otorgó el alcance read_accounts antes!
*
* Si está detrás de un proxy, debe configurar un proxy para cada conexión HTTP a continuación.Un proxy se puede configurar así:
 *
 * <pre>
 * Proxy proxy = new Proxy(Proxy.Type.HTTP, new InetSocketAddress("YOUR_PROXY_HOST", YOUR_PROXY_PORT));
 * Client client = ClientBuilder.newClient(new ClientConfig()
 *                  .connectorProvider(new HttpUrlConnectorProvider()
 *                  .connectionFactory(url -> (HttpURLConnection) url.openConnection(proxy))));
 * </pre>
 */
public class CallDbApiCashAccount {

	private static final String SESSION_ID = "JSESSIONID";
	private static final String BASE_URL = "https://simulator-api.db.com";

	private String codeVerifier;
	private String codeChallenge;
	private NewCookie sessionId;

	public static void main(String[] args) {
		CallDbApiCashAccount callDbApiCashAccount = new CallDbApiCashAccount();
		String fkn = "Your fkn from your generated Deutsche Bank test user account";
		String pin = "Your pin from your generated Deutsche Bank test user account";
		callDbApiCashAccount.generateRandomCodeVerifier();
		callDbApiCashAccount.createCodeChallenge();
		Response response = callDbApiCashAccount.authorizationRequest();
		Object [] responseAndRedirectUri = callDbApiCashAccount.redirectToLoginPage(response);
		response = callDbApiCashAccount.loginAndAuthorize(responseAndRedirectUri, fkn, pin);
		response = callDbApiCashAccount.grantAccess(response);
		String code = callDbApiCashAccount.getCode(response);
		response = callDbApiCashAccount.requestAccessTokensFromCode(code);
		String accessToken = callDbApiCashAccount.getAccessTokenFromJson(response);
		callDbApiCashAccount.callCashAccountsEndpoint(accessToken);
	}

	private void generateRandomCodeVerifier() {
		SecureRandom sr = new SecureRandom();
		byte[] code = new byte[32];
		sr.nextBytes(code);
		this.codeVerifier = java.util.Base64.getEncoder().encodeToString(code);
		System.out.println("Pre required Step 0.1 generated a random code verifier with value: " + this.codeVerifier);
	}

	private void createCodeChallenge() {
		try {
			byte[] bytes = codeVerifier.getBytes(StandardCharsets.UTF_8);
			MessageDigest md = MessageDigest.getInstance("SHA-256");
			md.update(bytes, 0, bytes.length);
			byte[] digest = md.digest();
			this.codeChallenge = Base64.encodeBase64URLSafeString(digest);
			System.out.println("Pre required Step 0.2 generated code challenge with the following value from the provided code verifier: " + this.codeChallenge);
		} catch (NoSuchAlgorithmException e2) {
			System.out.println("Wrong algorithm to encode: " + e2);
		}
	}

	private Response authorizationRequest() {
		WebTarget wt = ClientBuilder.newBuilder()
				.build()
				.target(BASE_URL + "/gw/oidc/authorize");
				Response response = wt.property(ClientProperties.FOLLOW_REDIRECTS, false)
						.queryParam("response_type", "code")
						.queryParam("client_id", "Your clientId from your generated client")
						.queryParam("redirect_uri", "One of your redirect URI(s) from your generated client")
						.queryParam("scope", "read_accounts")
						.queryParam("code_challenge_method", "S256")
						.queryParam("code_challenge", codeChallenge)
						.queryParam("state", "0.21581183640296075")
						.request()
						.get();

		updateSessionId(response);
		System.out.println("Step 1 executed authorizeRequest.");
		return response;
	}

	private Object[] redirectToLoginPage(Response response) {
		URI uri = response.getLocation();
		if(!uri.isAbsolute()) {
			uri = URI.create(BASE_URL).resolve(uri);
		}
		response =  ClientBuilder.newClient().target(uri)
				.property(ClientProperties.FOLLOW_REDIRECTS, false)
				.request()
				.cookie(sessionId).get();
		updateSessionId(response);
		System.out.println("Step 2 executed redirected to login page.");
		return new Object[] {response, uri};
	}

	private Response loginAndAuthorize(Object [] responseAndRedirectUri, String username, String password) {
		Response response = (Response) responseAndRedirectUri[0];
		URI uri = (URI) responseAndRedirectUri[1];
		String webPage = response.readEntity(String.class);
		String csrf = getCsrf(webPage);
		URI postUrl = getFormPostUrl(uri, webPage);
		Form form = new Form();
		form.param("username", username);
		form.param("password", password);
		form.param("_csrf", csrf);
		form.param("submit", "Login");
		response = ClientBuilder.newClient().target(postUrl)
				.property(ClientProperties.FOLLOW_REDIRECTS, false)
				.request()
				.cookie(sessionId)
				.post(Entity.entity(form, MediaType.APPLICATION_FORM_URLENCODED_TYPE));
		updateSessionId(response);
		if(response.getLocation().toString().contains("noaccess")
				|| response.getLocation().toString().contains("commonerror")
				|| response.getLocation().toString().contains("failure")) {
			System.out.println("Failed to login with username: \"" + username + "\"");
		}
		System.out.println("Step 3.1 login with fkn and pin and authorization done.");
		return  response;
	}

	private Response grantAccess(Response response) {
		URI uri = response.getLocation();
		if(!uri.isAbsolute()) {
			uri = URI.create(BASE_URL).resolve(uri);
		}
		response = ClientBuilder.newClient().target(uri)
				.property(ClientProperties.FOLLOW_REDIRECTS, false)
				.request().cookie(sessionId).get();
		updateSessionId(response);
		if (response.getStatusInfo().getFamily() == Response.Status.Family.SUCCESSFUL) {
			String webPage = response.readEntity(String.class);
			String csrf = getCsrf(webPage);
			URI postUrl = getFormPostUrl(uri, webPage);
			updateSessionId(response);
			Form form = new Form();
			form.param("user_oauth_approval", "true");
			form.param("_csrf", csrf);
			form.param("remember", "none");
			form.param("scope_read_accounts" , "read_accounts");
			response = ClientBuilder.newClient().target(postUrl).property(ClientProperties.FOLLOW_REDIRECTS, false)
					.request().cookie(sessionId).post(Entity.entity(form, MediaType.APPLICATION_FORM_URLENCODED_TYPE));
			System.out.println("Step 3.2 authorize access with requested scope read_accounts on consent screen.");
			return response;
		}
		return null;
	}

	private String getCode(Response response) {
		String responseLocationAfterGrantingAccess = response.getLocation().toString();
		String code = getCodeFromRedirect(responseLocationAfterGrantingAccess);
		System.out.println("Step 4 get the code after authorization and redirect: " + code);
		return code;
	}

	private Response requestAccessTokensFromCode(String code) {
		Form form = new Form();
		form.param("grant_type", "authorization_code");
		form.param("code", code);
		form.param("code_verifier", codeVerifier);
		form.param("client_id", "Your clientId from your generated client");
		form.param("redirect_uri", "One of your redirect URI(s) from your generated client");
		Response response = ClientBuilder.newClient()
				.target(BASE_URL + "/gw/oidc/token")
				.property(ClientProperties.FOLLOW_REDIRECTS, false)
				.request()
				.post(Entity.entity(form, MediaType.APPLICATION_FORM_URLENCODED_TYPE));
		updateSessionId(response);
		System.out.println("Step 5 request access token with given code: " + code + " and code verifier: " + codeVerifier);
		return response;
	}

	private String getAccessTokenFromJson(Response response) {
		String responseWithAccessToken  = response.readEntity(String.class);
		ObjectMapper mapper = new ObjectMapper();
		JsonNode jsonNode = null;
		try {
			jsonNode = mapper.readTree(responseWithAccessToken);
		} catch (JsonProcessingException e) {
			e.printStackTrace();
		}
		String accessToken = jsonNode.get("access_token").textValue();
		System.out.println("Step 6 extracted Bearer access token with value: " + accessToken);
		return accessToken;
	}

	private void callCashAccountsEndpoint(String accessToken) {
		WebTarget wt = ClientBuilder.newBuilder()
				.build()
				.target(BASE_URL + "/gw/dbapi/banking/cashAccounts/v2");
		Response response = wt.request()
				.header("Authorization", "Bearer " + accessToken)
				.accept(MediaType.APPLICATION_JSON)
				.get();
		System.out.println("Step 7 calling dbAPI cashAccounts endpoint done. The JSON response is:");
		String jsonResponse = response.readEntity(String.class);
		System.out.println(jsonResponse);
	}

	private void updateSessionId(Response response) {
		NewCookie cookie = response.getCookies().get(SESSION_ID);
		if(cookie != null) {
			sessionId = cookie;
		}
	}

	private String getCsrf(String webPage) {
		Pattern p = Pattern.compile(" name=\"_csrf\" value=\"(.*?)\"");
		Matcher m = p.matcher(webPage);
		if ( m.find() ) {
			return m.group(1);
		}
		return null;
	}

	private URI getFormPostUrl(URI target, String webPage) {
		Pattern pattern = Pattern.compile("action=\"(.+?)\"");
		Matcher matcher = pattern.matcher(webPage);
		if ( matcher.find() ) {
			String uf = matcher.group(1);
			URI uri = URI.create(uf);
			if(!uri.isAbsolute()) {
				URI targetUri = target.resolve(uri);
				return targetUri;
			}
			return uri;
		}
		return null;
	}

	private String getCodeFromRedirect(String uri) {
		return getTokenFromString(uri, "code=([\\d\\w\\.-]+)&");
	}

	private String getTokenFromString(String uri, String pattern) {
		Pattern tokenPattern = Pattern.compile(pattern);
		Matcher tokenMatcher = tokenPattern.matcher(uri);
		if (tokenMatcher.find()) {
			return tokenMatcher.group(1);
		}
		return null;
	}

}
