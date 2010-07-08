import logging
import urlparse

from docutils import nodes
from docutils.transforms import Transform


logger = logging.getLogger(__name__)


class References(Transform):

    """
    Rewrite references to links in output.
    Ie. strip srcformat 
    """

    settings_spec = (
            )

    default_priority = 500

    def apply(self):
        doc = self.document

        refs = doc.traverse(nodes.reference) 

        # TODO: settings
        srcfmt = 'rst'

        for ref in refs:
            s,h,p,r,q,f = urlparse.urlparse(ref['refuri'])
            if not h:
                if p.endswith('.'+srcfmt):
                    p = p[:-len('.'+srcfmt)] 
                    ref['refuri'] = urlparse.urlunparse((s,h,p,r,q,f))
            logger.info(ref)



