import { Layout } from "./Layout.tsx";

export function Privacy() {
  return (
    <Layout privacy={false} footer={<a href="/">Volver al inicio</a>}>
      <div className="page doc">
        <h1>Privacidad</h1>
        <p className="lead">
          Puedes usar todos los cursos sin cuenta. Una cuenta es opcional y
          sirve para llevar tu progreso a otro navegador. Esta página dice qué
          se guarda, cuánto tiempo y cómo borrarlo.
        </p>

        <h2>Sin cuenta</h2>
        <ul>
          <li>
            Tu progreso (lecciones hechas, el código de tus ejercicios, tus
            reflexiones y tus preferencias) se guarda solo en tu navegador, en{" "}
            <code>localStorage</code>. No sale de él. Borrar los datos del sitio
            en tu navegador lo borra.
          </li>
          <li>
            Esta página no hace ninguna petición a nuestro servidor por tu
            progreso. La única petición propia es <code>/run</code>, cuando
            pulsas Ejecutar o Comprobar en un ejercicio. Ver «Al ejecutar
            código».
          </li>
        </ul>

        <h2>Con cuenta</h2>
        <p>
          Entras con Google o con GitHub. No usamos contraseña, y al proveedor
          solo le pedimos tu identificador numérico: no recibimos ni guardamos
          tu correo, tu nombre ni tu foto. El proveedor sí sabe que entraste en
          este sitio.
        </p>
        <p>
          Guardamos, con un identificador al azar que no es tu identificador del
          proveedor:
        </p>
        <ul>
          <li>El proveedor con el que entraste y tu identificador en él.</li>
          <li>El día en que creaste la cuenta y el día de tu última visita.</li>
          <li>Las lecciones que terminaste.</li>
          <li>
            De cada ejercicio, el último código que escribiste, cuántas pistas
            viste, cuántas veces lo comprobaste y si lo resolviste.{" "}
            <strong>
              El código se guarda tal como lo escribes: no pongas en él nada que
              no quieras guardar.
            </strong>
          </li>
          <li>
            Tu avance en las lecciones: pasos escuchados, último paso, tus
            apuestas, el repaso espaciado y los hitos que marcaste.
          </li>
          <li>
            Tu XP: cada vez que ganas XP se guarda el momento, de dónde viene y
            cuánto fue, y se borra a los 14 días. Con eso sale tu racha: el
            último día con XP, la racha más larga y los días de gracia que te
            quedan. También guardamos tu zona horaria, para saber qué día es
            para ti.
          </li>
          <li>
            Tus amigos, si invitas a alguien o aceptas una invitación. Cada uno
            ve de ti tu racha, si practicaste hoy y tu XP de la semana; no ve tu
            nombre, porque no lo tenemos. Quitar a un amigo lo borra para los
            dos.
          </li>
          <li>
            Si activas el aviso de racha, la dirección que tu navegador nos da
            para enviarte notificaciones y sus claves de cifrado. Las usamos
            solo para el aviso, que sale una vez al día y solo si tienes racha y
            aún no ganaste XP ese día. El servicio de notificaciones de tu
            navegador (Google, Mozilla o Apple) ve que recibes un aviso de este
            sitio, pero no su contenido. Puedes quitarlo desde la página Amigos
            o en los ajustes de tu navegador.
          </li>
          <li>
            Una sesión: una cookie <code>qg_auth</code> que solo sirve para
            saber que eres tú. En el servidor guardamos únicamente una huella
            del valor de la cookie.
          </li>
        </ul>
        <p>
          <strong>Lo que escribes en las reflexiones no se envía.</strong> Se
          queda en tu navegador, también con cuenta.
        </p>

        <h2>Cuánto tiempo</h2>
        <ul>
          <li>La sesión dura 30 días. Cerrar la sesión la borra antes.</li>
          <li>
            La cuenta y todo lo que guarda se borran si pasan 24 meses sin que
            la visites.
          </li>
          <li>Puedes borrarla cuando quieras, como se explica abajo.</li>
        </ul>

        <h2>Al ejecutar código</h2>
        <p>
          Ejecutar o comprobar un ejercicio envía tu código a nuestro servidor,
          que lo ejecuta y devuelve el resultado. El código no se guarda por
          eso. Sí se anota, con o sin cuenta, una fila por ejecución: el
          momento, el ejercicio, si pasó o falló, los nombres de los casos que
          fallaron, el tipo de error, cuántas pistas habías visto, cuánto tardó
          y cuántos bytes ocupaba el código. No lleva el código ni lo que
          imprimió. Si tenías cuenta, la fila apunta a ella; si no, no apunta a
          nadie. Se borra a los 180 días. Con cuenta, borrar la cuenta borra
          también estas filas.
        </p>
        <p>
          No guardamos tu dirección IP. Para limitar el uso abusivo, el servidor
          cuenta las peticiones con un código derivado de la IP o de la cuenta
          que cambia cada día y no permite volver a ella. Sin cuenta, la primera
          ejecución pide una comprobación de Cloudflare Turnstile para saber que
          eres una persona, y el servidor te da una cookie{" "}
          <code>qg_session</code> de 8 horas que no te identifica.
        </p>
        <p>
          Las tipografías y las fórmulas de KaTeX salen de este mismo sitio, sin
          servicios de terceros. El script de Cloudflare Turnstile se descarga
          de Cloudflare solo cuando hace falta la comprobación, y Cloudflare ve
          entonces tu dirección IP.
        </p>

        <h2>Cómo borrar tus datos</h2>
        <ul>
          <li>
            <strong>Con cuenta:</strong> abre el menú <em>Cuenta</em> de la
            esquina superior, pulsa <em>Borrar mi cuenta</em> y confirma. Se
            borran de inmediato la cuenta, tu identificador del proveedor, las
            sesiones, tu progreso y tus ejecuciones. No se puede deshacer.
          </li>
          <li>
            <strong>La copia de tu navegador</strong> no se toca al borrar la
            cuenta. Para borrarla, elimina los datos del sitio en los ajustes de
            tu navegador.
          </li>
          <li>
            Para dejar de compartir datos con el proveedor, revoca el acceso a
            este sitio en los ajustes de tu cuenta de Google o de GitHub.
          </li>
        </ul>
      </div>
    </Layout>
  );
}
